import inspect
import numpy
import collections.abc
from collections import deque
import io
from typing import Optional, Any, List, Dict, Union, Sequence
import ovito
from ovito.nonpublic import RefTarget, RenderSettings
from ovito.data import DataObject, Property, ElementType
from ovito.pipeline import (
    Pipeline,
    PipelineNode,
    Modifier,
    ModifierInterface,
    ModificationNode,
)
from ovito.vis import ColorLegendOverlay, DataVis, Viewport, ViewportOverlay
from traits.api import HasTraits
import traits.trait_base
from dataclasses import dataclass


def format_pipeline_id(pipeline_id: int) -> str:
    if len(ovito.scene.pipelines) == 1:
        return ""
    # Offset to have pipeline counting start at 1 for the user
    return str(pipeline_id + 1)


def format_property_value(value: Any) -> str:
    """Produces a pretty string representation of a Python object or value."""

    # Format small NumPy arrays as Python lists.
    if isinstance(value, numpy.ndarray):
        # Linear arrays of length 4 and shorter.
        if value.ndim == 1 and len(value) <= 4:
            return repr(value.tolist())
        # Matrix arrays of shape (3,4).
        if value.shape == (3, 4):
            return repr(value.tolist())

    # Make sure the fully qualified type name is being used.
    t = type(value)
    if t.__name__ != t.__qualname__:
        result = repr(value)
        if result.startswith(t.__name__):
            result = t.__qualname__ + result[len(t.__name__) :]
        return result

    # Format floating-point values using a slightly reduced precision to avoid ugly rounding effects (e.g. "0.3799999999999999" instead of "0.38").
    if isinstance(value, float):
        s = f"{value:.12g}"
        if "." not in s and "e" not in s:
            s += ".0"  # When fixed-point notation is used to format the result, make sure it always includes at least one digit past the decimal point.
        return s

    # Unlike native Ovito objects, HasTraits objects such as FileReaderInterface and ModifierInterface have no
    # customized __repr__ implementation. Emit a proper call statement to the class constructor here.
    if isinstance(value, HasTraits):
        return f"{type(value).__name__}()"

    # In all other cases, fall back to standard formatting using repr() function.
    return repr(value)


def property_value_diff(
    stream: io.StringIO,
    ref_value: Any,
    value: Any,
    include_vis: bool,
    force_instantiation: bool = False,
    prefer_oneliner: bool = False,
    no_direct_assignments: bool = False,
) -> List[str]:
    """Compares two objects or values of the same type for equality."""

    # NumPy arrays cannot be compared using the == operator. Need to use array_equal() function instead.
    if isinstance(ref_value, numpy.ndarray) and isinstance(value, numpy.ndarray):
        if not numpy.array_equal(ref_value, value) and not no_direct_assignments:
            return [f" = {format_property_value(value)}"]
        return []

    # Skip pipeline reference fields
    if isinstance(value, Pipeline):
        return [" = <pipeline>"]

    # Implement element-wise deep comparison for list-like sequence types.
    if (
        isinstance(ref_value, collections.abc.Sequence)
        and isinstance(value, collections.abc.Sequence)
        and not isinstance(ref_value, (tuple, str))
    ):
        result = []
        if len(ref_value) == len(value):
            for index, (ref_item, item) in enumerate(zip(ref_value, value)):
                for diff in property_value_diff(
                    stream, ref_item, item, include_vis, prefer_oneliner=prefer_oneliner
                ):
                    result.append(f"[{index}]{diff}")
        elif len(ref_value) < len(value) and isinstance(value[0], RefTarget):
            for index, (ref_item, item) in enumerate(
                zip(ref_value, value[: len(ref_value)])
            ):
                for diff in property_value_diff(
                    stream, ref_item, item, include_vis, prefer_oneliner=prefer_oneliner
                ):
                    result.append(f"[{index}]{diff}")
            for item in value[len(ref_value) :]:
                if isinstance(item, RefTarget):
                    statements = generate_object_instantiation(
                        stream, "obj", None, item, include_vis
                    )
                    if isinstance(statements, str):
                        # Generate in-place modifier instantiation:
                        result.append(f".append({statements})")
                    else:
                        # Generate code with a temporary variable:
                        result.append("\n".join(statements) + "\n.append(obj)")
                else:
                    result.append(f".append({format_property_value(item)})")
        elif not no_direct_assignments:
            result.append(f" = {format_property_value(value)}")
        return result

    # Compare two OVITO objects based on their attributes.
    if (ref_value is None or isinstance(ref_value, (RefTarget, HasTraits))) and (
        value is None or isinstance(value, (RefTarget, HasTraits))
    ):
        result = []
        if type(ref_value) is not type(value) or force_instantiation:
            result.append(f" = {format_property_value(value)}")
        if value is None:
            return result
        only_property_assignments = len(result) == 1
        obj_props = get_object_modified_properties(
            stream, ref_value, value, include_vis
        )
        for attr_name, attr_value in obj_props.items():
            for diff in attr_value:
                result.append(f".{attr_name}{diff}")
                if not diff.startswith(" = "):
                    only_property_assignments = False

        # If the statements are direct property value assignments,
        # reformat it as a single constructor call.
        if only_property_assignments:
            arguments = []
            for stat in result[1:]:
                arg = stat[1:]
                if not prefer_oneliner and len(result) > 2:
                    arg = "\n    " + arg
                arguments.append(arg)
            result = [f" = {type(value).__qualname__}({', '.join(arguments)})"]

        return result

    # Use built-in comparison operator otherwise.
    if ref_value != value and not no_direct_assignments:
        return [f" = {format_property_value(value)}"]

    return []


def generate_object_instantiation(
    stream: io.StringIO,
    variable_name: str,
    ref_obj: Any,
    obj: Any,
    include_vis: bool = False,
    prefer_oneliner: bool = False,
) -> List[str]:
    """Generates code that instantiates a new object and sets its parameters."""

    statements = property_value_diff(
        stream,
        ref_obj,
        obj,
        include_vis,
        force_instantiation=True,
        prefer_oneliner=prefer_oneliner,
    )
    if len(statements) == 1:
        # Generate a one-liner.
        assert statements[0].startswith(" = ")
        return statements[0][len(" = ") :]
    else:
        src_lines = []
        for stmt in statements:
            src_lines.append(f"{variable_name}{stmt}")
        return src_lines


def get_object_modified_properties(
    stream: io.StringIO,
    ref_obj: Union[RefTarget, HasTraits, None],
    obj: Union[RefTarget, HasTraits],
    include_vis: bool = False,
) -> Dict[str, str]:
    """Builds a list of properties of the given object which were modified by the user."""

    attr_list = {}

    # Unless the caller has already provided it, create a default-initialized object instance of the same type as the input object.
    # It will be used to detect which object parameters were modified by the user.
    if not ref_obj:
        # This object construction may fail with a TypeError if the class does not define a public constructor (e.g. the Property class).
        try:
            ref_obj = type(obj)()
        except TypeError:
            return attr_list
        # Some objects have explicit reference values stored for certain property fields, which can be used to detect changes made by the user.
        if isinstance(obj, RefTarget):
            obj._copy_initial_parameters_to_object(ref_obj)

    # Iterate over all attributes of the input object.
    if isinstance(obj, RefTarget):
        for attr_name in obj.__dir__():
            # Determine if the attribute is an object property.
            attr = inspect.getattr_static(obj, attr_name)
            if isinstance(attr, property):
                # Skip hidden object attributes which are not documented.
                if not attr.__doc__:
                    continue

                # Get the property value.
                value = getattr(obj, attr_name)
                # Get the corresponding value of the default-initialized reference object.
                ref_value = getattr(ref_obj, attr_name, value)

                # Skip visualization elements unless they should be included and are not disabled.
                if isinstance(value, ovito.vis.DataVis) and not include_vis:
                    continue

                # Skip data objects.
                if isinstance(value, ovito.data.DataObject):
                    continue

                # Detect read-only properties. Do not generate statements that directly assign a value to a read-only property.
                is_readonly = hasattr(attr, "fset") and attr.fset is None

                # Add attribute to the output list if its value does not exactly match the default value.
                diff = property_value_diff(
                    stream,
                    ref_value,
                    value,
                    include_vis,
                    no_direct_assignments=is_readonly,
                )
                if diff:
                    attr_list[attr_name] = diff

    elif isinstance(obj, HasTraits):
        # Get the values of all non-transient traits.
        # See https://docs.enthought.com/traits/traits_api_reference/has_traits.html#traits.has_traits.HasTraits.trait_get
        params = obj.trait_get(transient=traits.trait_base.is_none)
        for attr_name, value in params.items():
            # Get the corresponding value of the default-initialized reference object.
            ref_value = getattr(ref_obj, attr_name, value)

            # Skip visualization elements unless they should be included and are not disabled.
            if isinstance(value, ovito.vis.DataVis) and not include_vis:
                continue

            # Skip data objects.
            if isinstance(value, ovito.data.DataObject):
                continue

            # Add attribute to the output list if its value does not exactly match the default value.
            diff = property_value_diff(stream, ref_value, value, include_vis)
            if diff:
                attr_list[attr_name] = diff

    if hasattr(obj, "__codegen__"):
        # Give all classes in the hierarchy the chance to filter or amend the generated statements.
        clazz = type(obj)
        while clazz is not RefTarget:
            if "__codegen__" in clazz.__dict__:
                literal_code = clazz.__codegen__(obj, attr_list)
                if literal_code:
                    stream.write(literal_code)
            if not clazz.__bases__:
                break
            clazz = clazz.__bases__[0]

    return attr_list


def is_property_assignment(statement: str) -> bool:
    """Helper function which decides whether a code statement is a value assignment to a property field
    or rather a method call statement."""
    equal_pos = statement.find("=")
    parenthesis_pos = statement.find("(")
    return equal_pos >= 0 and (parenthesis_pos == -1 or parenthesis_pos > equal_pos)


def codegen_modifier(
    stream: io.StringIO,
    modifier: Modifier,
    include_vis: bool,
    group: Any,
    pipeline_id,
    modifier_name: Optional[str],
) -> None:
    """Generates code lines for setting up a modifier and its parameters."""

    if isinstance(modifier, ovito.modifiers.PythonModifier):
        # Do not emit code if Python script modifier is disabled.
        if not modifier.enabled or (group is not None and group.enabled is False):
            stream.write(f"\n\n# Skipping disabled modifier '{modifier.object_title}'")
            return

        if modifier.delegate is not None:
            # Unless it is a predefined Python modifier included with OVITO Pro, copy the original source
            # code into the generated script.
            if not type(modifier.delegate).__module__.startswith(
                "ovito._extensions.scripts."
            ):
                if len(modifier.script) != 0:
                    stream.write(
                        f"\n\n# Source code of custom modifier '{modifier.object_title}':\n"
                    )
                    stream.write(modifier.script)
                else:
                    # Generate an import statement for the module the modifier class is defined in.
                    stream.write(
                        f"\n\nfrom {type(modifier.delegate).__module__} import *"
                    )
            codegen_modifier_builtin(
                stream,
                modifier.delegate,
                include_vis,
                group,
                modifier.object_title,
                pipeline_id,
                modifier_name,
            )
        else:
            # Generate code that inserts a user-defined modify() function into the pipeline.
            codegen_user_modify_func(
                stream, modifier, include_vis, group, pipeline_id, modifier_name
            )
    else:
        codegen_modifier_builtin(
            stream,
            modifier,
            include_vis,
            group,
            modifier.object_title,
            pipeline_id,
            modifier_name,
        )


def codegen_modifier_builtin(
    stream: io.StringIO,
    modifier: Union[Modifier, ModifierInterface],
    include_vis: bool,
    group: Any,
    title: str,
    pipeline_id: int,
    modifier_name: Optional[str],
) -> None:
    """Generates code lines for setting up a modifier and its parameters."""

    # Create a default-initialized modifier instance.
    # It will be used to detect which modifier parameters were modified by the user.
    default_modifier = type(modifier)()

    # Temporarily insert it into a pipeline in order to let the modifier initialize itself based on the current pipeline state.
    node = modifier.some_modification_node if isinstance(modifier, Modifier) else None
    if node:
        default_node = default_modifier.create_modification_node()
        default_node.input = node.input
        default_node.modifier = default_modifier
        default_modifier.initialize_modifier(default_node, None)

    if group is None:
        stream.write(f"\n\n# {title}:\n")
    else:
        stream.write(f"\n\n# {group.object_title} - {title}:\n")
    if modifier_name:
        statements = generate_object_instantiation(
            stream, modifier_name, default_modifier, modifier, include_vis
        )
    else:
        statements = generate_object_instantiation(
            stream, "mod", default_modifier, modifier, include_vis
        )
    if isinstance(statements, str):
        # Generate in-place modifier instantiation:
        if modifier_name:
            modifier_statements = f"{modifier_name} = {statements}"
        else:
            modifier_statements = f"pipeline{format_pipeline_id(pipeline_id)}.modifiers.append({statements})"
    else:
        # Generate code with a temporary variable holding the modifier.
        # The modifier is first constructed and initialized, then inserted into the pipeline.
        # The list of statements may consist of value assignments to properties of the modifier
        # and calls to methods of the modifier. We place property assignments BEFORE the
        # insertion of the modifier into the pipeline and method calls AFTER the insertion.
        # This order is required in some cases (e.g. GenerateTrajectoryLinesModifier) so that the
        # modifier has access to the pipeline data when a method is called.
        assignments = [
            statement for statement in statements if is_property_assignment(statement)
        ]
        method_calls = [
            statement
            for statement in statements
            if not is_property_assignment(statement)
        ]
        if modifier_name:
            if len(method_calls) != 0:
                raise RuntimeError("Method calls not implemented for shared modifiers!")
            all_statements = assignments
        else:
            all_statements = (
                assignments
                + [f"pipeline{format_pipeline_id(pipeline_id)}.modifiers.append(mod)"]
                + method_calls
            )
        modifier_statements = "\n".join(all_statements)
    # Named modifiers are shared and should not be disabled like this
    if not modifier_name and group is not None and not group.enabled:
        stream.write(
            "# Leaving this modifier out, because its modifier group is disabled.\n"
        )
        stream.write("if False:\n")
        # Apply correct indentation to the generated statements.
        stream.write("    " + modifier_statements.replace("\n", "\n    "))
    else:
        stream.write(modifier_statements)


def codegen_user_modify_func(
    stream: io.StringIO,
    modifier: ovito.modifiers.PythonModifier,
    include_vis: bool,
    group: Any,
    pipeline_id: int,
    modifier_name: Optional[str],
) -> None:
    """Generates code lines for setting up a user-defined modifier that consists of a modify() function."""

    # Do not emit code if Python script modifier is disabled.
    # Named modifiers are shared and should not be disabled like this
    if not modifier.enabled or (
        not modifier_name and group is not None and group.enabled is False
    ):
        stream.write(f"\n\n# Skipping disabled modifier '{modifier.object_title}'")
        return

    # Copy the full script source code entered by the user.
    if len(modifier.script) != 0:
        stream.write(
            f"\n\n# User-defined modifier function '{modifier.object_title}':\n"
        )
        stream.write(modifier.script)
    else:
        stream.write(f"\n\n# Python modifier function '{modifier.object_title}':")
    modifier_func_name = "modify"
    if hasattr(modifier.function, "__name__"):
        modifier_func_name = modifier.function.__name__
    if not modifier.kwargs:
        if modifier_name:
            stream.write(f"\n{modifier_name} = {modifier_func_name}")
        else:
            stream.write(
                f"\npipeline{format_pipeline_id(pipeline_id)}.modifiers.append({modifier_func_name})"
            )
    else:
        # Pass the values of the user-defined parameters to the modifier function using
        # partial function parameter binding.
        stream.write("\nimport functools")
        kwargs_list = []
        for key, value in modifier.kwargs.items():
            if isinstance(value, RefTarget):
                statements = generate_object_instantiation(
                    stream, key, type(value)(), value, include_vis, prefer_oneliner=True
                )
            else:
                statements = format_property_value(value)
            if isinstance(statements, str):
                # Generate in-place instantiation:
                kwargs_list.append(f"{key} = {statements}")
            else:
                # Generate code with a temporary variable:
                stream.write("\n" + "\n".join(statements))
                kwargs_list.append(f"{key} = {key}")

        if len(kwargs_list) > 2:
            kwargs_list = ["\n    " + arg for arg in kwargs_list]

        if modifier_name:
            stream.write(
                f"\n{modifier_name} = functools.partial({modifier_func_name}, {', '.join(kwargs_list)})"
            )
        else:
            stream.write(
                f"\npipeline{format_pipeline_id(pipeline_id)}.modifiers.append(functools.partial({modifier_func_name}, {', '.join(kwargs_list)}))"
            )


def find_object_prefix_recursive(
    obj, needle, make_mutable: bool = False
) -> Optional[str]:
    """Recursively searches a given object in the object hierarchy of a DataCollection."""
    if not obj or not isinstance(obj, RefTarget):
        return None
    if obj is needle:
        return ""
    for search_pass in (1, 2, 3, 4):
        for attr_name in obj.__dir__():
            # Determine if the attribute is an object property.
            attr = inspect.getattr_static(obj, attr_name)
            if isinstance(attr, property):
                # Skip underscore property fields.
                if attr_name.endswith("_"):
                    continue

                # Skip hidden object attributes which are not publicy documented.
                if not attr.__doc__:
                    continue

                try:
                    # Read the current property value (this may raise a KeyError exception).
                    value = getattr(obj, attr_name)

                    # Append '_' suffix to attribute name if property accesses a data object to be modified.
                    # Be careful not to accidentally read the value of the '_' version of the attribute, because this triggers a call to make_mutable()!
                    if (
                        make_mutable
                        and isinstance(value, DataObject)
                        and (attr_name + "_") in obj.__dir__()
                    ):
                        attr_name = attr_name + "_"

                    if search_pass == 1:
                        if value is needle:
                            # We have found the target in the object hierarchy.
                            return "." + attr_name
                    elif search_pass == 2:
                        if isinstance(value, RefTarget):
                            # Continue with recursive search.
                            path = find_object_prefix_recursive(
                                value, needle, make_mutable
                            )
                            if path is not None:
                                return "." + attr_name + path
                    elif search_pass == 3:
                        if isinstance(value, collections.abc.Mapping):
                            # Continue with recursive search.
                            for key in value.keys():
                                if not isinstance(key, str):
                                    continue
                                subobj = value[key]
                                if not isinstance(subobj, RefTarget):
                                    if subobj is None:
                                        continue
                                    else:
                                        break
                                path = find_object_prefix_recursive(
                                    subobj, needle, make_mutable
                                )
                                if path is not None:
                                    if make_mutable:
                                        key += "_"
                                    return f".{attr_name}['{key}']" + path
                    else:
                        if isinstance(
                            value, collections.abc.Sequence
                        ) and not isinstance(value, str):
                            # Continue with recursive search.
                            for index in range(len(value)):
                                subobj = value[index]
                                if not isinstance(subobj, RefTarget):
                                    if subobj is None:
                                        continue
                                    else:
                                        break
                                path = find_object_prefix_recursive(
                                    subobj, needle, make_mutable
                                )
                                if path is not None:
                                    # Special handling of ElementType: Use Property.type_by_id() method.
                                    if (
                                        isinstance(obj, Property)
                                        and isinstance(subobj, ElementType)
                                        and attr_name == "types"
                                    ):
                                        if make_mutable:
                                            return f".type_by_id_({subobj.id})" + path
                                        else:
                                            return f".type_by_id({subobj.id})" + path

                                    return f".{attr_name}[{index!r}]" + path

                except KeyError:
                    pass
    return None


def find_visual_element_prefix(
    pipeline: Pipeline, vis: DataVis, use_pipeline_output: bool
) -> Optional[str]:
    """Builds the hierarchical Python object expression that references the given visual element in a DataCollection."""
    assert vis is not None
    if use_pipeline_output:
        # Take data collection from the end of the pipeline:
        try:
            data = pipeline.compute()
        except RuntimeError:
            return None
    else:
        # Take data collection from the head of the pipeline (FileSource):
        if not pipeline.source or not hasattr(pipeline.source, "data"):
            return None
        data = pipeline.source.data
    return find_object_prefix_recursive(data, vis)


def codegen_trajectory_playback(
    stream: io.StringIO,
    pipeline: Pipeline,
    ref_obj: Optional[PipelineNode],
    pipeline_id: int,
):
    """Generates Python statements for pipeline / file source playback rate."""
    has_header = False

    def write_header():
        nonlocal has_header, stream
        header = "\n\n# Trajectory playback rate"
        if not has_header:
            stream.write(header)
            has_header = True

    # Unless the caller has already provided it, create a default-initialized object instance of the same type as the input object.
    # It will be used to detect which object parameters were modified by the user.
    if not ref_obj:
        ref_obj = type(pipeline.source)()

    static_frame = False
    try:
        frame = pipeline.source.static_frame
        ref_frame = ref_obj.static_frame
        if frame is not None and (frame != ref_frame):
            static_frame = True
            write_header()
            stream.write(
                f"\npipeline{format_pipeline_id(pipeline_id)}.source.static_frame = {frame}"
            )
    # Not all sources support static_frame. If the source does not support it, we just ignore it.
    except AttributeError:
        return
    if static_frame:
        return

    # Apply playback ratio and start time only if the playback is not static frame.
    try:
        ratio = pipeline.source.playback_ratio
        start = pipeline.source.playback_start_time

        ref_ratio = ref_obj.playback_ratio
        ref_start = ref_obj.playback_start_time
    # Not all sources support playback ratios. If the source does not support it, we just ignore it.
    except AttributeError:
        return

    if ratio != ref_ratio:
        write_header()
        stream.write(
            f"\npipeline{format_pipeline_id(pipeline_id)}.source.playback_ratio = '{ratio}'"
        )
    if start != ref_start:
        write_header()
        stream.write(
            f"\npipeline{format_pipeline_id(pipeline_id)}.source.playback_start_time = {format_property_value(start)}"
        )


def codegen_pipeline_transformation(
    stream: io.StringIO,
    pipeline: Pipeline,
    ref_obj: Optional[Pipeline],
    pipeline_id: int,
):
    """Generates Python statements for pipeline transformations."""
    has_header = False

    def write_header():
        nonlocal has_header, stream
        header = "\n\n# Visual pipeline transformations"
        if not has_header:
            stream.write(header)
            has_header = True

    # Unless the caller has already provided it, create a default-initialized object instance of the same type as the input object.
    # It will be used to detect which object parameters were modified by the user.
    if not ref_obj:
        ref_obj = Pipeline()

    # Rotation of the current pipeline.
    rotation = pipeline.rotation
    # Rotation of the reference pipeline.
    ref_rotation = ref_obj.rotation
    # Generate statement if rotation is not the default rotation.
    if not numpy.array_equal(rotation, ref_rotation):
        write_header()
        stream.write(
            f"\npipeline{format_pipeline_id(pipeline_id)}.rotation = {format_property_value(rotation)}"
        )

    # Translation of the current pipeline.
    translation = pipeline.translation
    # Translation of the reference pipeline.
    ref_translation = ref_obj.translation
    # Generate statement if translation is not the default translation.
    if not numpy.array_equal(translation, ref_translation):
        write_header()
        stream.write(
            f"\npipeline{format_pipeline_id(pipeline_id)}.translation = {format_property_value(translation)}"
        )


@dataclass
class Node:
    node: ModificationNode
    parents: list[int]
    children: list[int]
    pipelines: Optional[list[Pipeline]] = None

    def add_parent(self, parent):
        if parent not in self.parents:
            self.parents.append(parent)

    def add_child(self, child):
        if child not in self.children:
            self.children.append(child)

    def add_pipeline(self, pipeline: Pipeline):
        if self.pipelines is None:
            self.pipelines = [pipeline]
        else:
            self.pipelines.append(pipeline)


@dataclass
class ModificationNode(Node):
    shared: Optional[Union[Modifier, ModifierInterface, ViewportOverlay]] = None

    def __str__(self):
        return str(self.node.modifier.object_title)


@dataclass
class InputNode(Node):
    pipeline: Optional[Pipeline] = None

    def __str__(self):
        return "File source: " + str(self.node.object_title)


@dataclass
class EndNode(Node):
    def __str__(self):
        return f"End node of {self.parents}"


class SharedModifiers(dict):
    def get_name(self, node):
        mod_name = str(node).lower().strip("()").replace(" ", "_")
        c = 0
        for value in self.values():
            if value.startswith(mod_name):
                c += 1
        if c > 0:
            mod_name += f"_{c+1}"
        return mod_name


class Network(dict):
    def __init__(self) -> None:
        super().__init__()

    def get_pipeline_roots(self):
        for key, value in self.items():
            if isinstance(value, InputNode):
                yield key

    def add_node(
        self,
        node: ModificationNode,
        prev_node: Optional[ModificationNode],
        pipeline: Pipeline,
    ):
        inp = id(node.input) if hasattr(node, "input") else None
        prev = id(prev_node) if prev_node is not None else None
        if id(node) not in self:
            if inp is None:
                self[id(node)] = InputNode(node, [inp], [prev], pipeline=pipeline)
            else:
                shared = None
                if len(node.modifier.get_modification_nodes()) > 1:
                    shared = node.modifier
                self[id(node)] = ModificationNode(node, [inp], [prev], shared=shared)
        else:
            self[id(node)].add_parent(inp)
            self[id(node)].add_child(prev)
            self[id(node)].add_pipeline(pipeline)

    def add_pipeline(self, pipeline: Pipeline):
        node = pipeline.head
        prev_node = EndNode(Node, [id(node)], [None])
        self[id(prev_node)] = prev_node
        while node != pipeline.source:
            self.add_node(node, prev_node, pipeline)
            prev_node = node
            node = node.input
        self.add_node(node, prev_node, pipeline)

    def _flatten_helper(self, start_node):
        node = self[start_node]
        queue = [[node]]
        while len(node.children) == 1 and node.children[0] is not None:
            node = self[node.children[0]]
            queue[0].append(node)

        for child in node.children:
            if child is not None:
                sub_queue = self._flatten_helper(child)
                queue.append(sub_queue)
        return queue

    def flatten(self):
        # pipelines = {}
        pipelines = []
        for key, value in self.items():
            if all(p is None for p in value.parents):
                fifo = self._flatten_helper(key)
                pipelines.append(fifo)
        return pipelines


def find_overlay_modification_node(overlay: ViewportOverlay):
    node = overlay.pipeline.head
    while node != overlay.pipeline.source:
        for mod_node in overlay.modifier.get_modification_nodes():
            if node == mod_node:
                return node
        node = node.input
    assert False


# First pass over viewports collects the modifiers required for the viewport overlays
def viewports_first_pass(
    scene: ovito.scene, modifier_network: Network, shared_modifiers: SharedModifiers
) -> None:
    for viewport in scene.viewports:
        for overlay in viewport.overlays:

            if not isinstance(overlay, ColorLegendOverlay):
                continue
            if overlay.modifier:
                node = find_overlay_modification_node(overlay)

                assert id(node) in modifier_network
                network_node = modifier_network[id(node)]

                if network_node.shared is None:
                    network_node.shared = node.modifier

                # if id(network_node.shared) not in shared_modifiers:
                #     shared_modifiers[id(network_node.shared)] = shared_modifiers.get_name(network_node)


def find_key_from_value(d: dict, value: Any):
    for k, v in d.items():
        if v == value:
            return k
    assert False


class ViewportStatementFormatter:
    def __init__(self, viewport: Viewport, shared_modifiers: SharedModifiers):
        self.viewport = viewport
        self.shared_modifiers = shared_modifiers
        self.overlay_index = 0

    def __call__(
        self,
        stat: str,
    ) -> str:
        global pipeline_map

        if "<modifier>" in stat:
            assert self.overlay_index < len(self.viewport.overlays)
            overlay = self.viewport.overlays[self.overlay_index]
            node = find_overlay_modification_node(overlay)
            assert id(node.modifier) in self.shared_modifiers
            stat = stat.replace(
                "<modifier>", f"{self.shared_modifiers[id(node.modifier)]}"
            )
        if "<color_mapping_source>" in stat:
            assert self.overlay_index < len(self.viewport.overlays)
            overlay = self.viewport.overlays[self.overlay_index]
            rep_string = ""
            for pipeline_id, pipeline in pipeline_map.items():
                prefix = find_replaced_visual_element_prefix(
                    pipeline, overlay.color_mapping_source
                )
                if prefix:
                    rep_string = (
                        f"pipeline{format_pipeline_id(pipeline_id)}.compute(){prefix}"
                    )
                    break
            assert rep_string
            stat = stat.replace("<color_mapping_source>", rep_string)
        if "<property>" in stat:
            assert self.overlay_index < len(self.viewport.overlays)
            overlay = self.viewport.overlays[self.overlay_index]
            stat = stat.replace("<property>", f'"{overlay.property}"')
        if "<pipeline>" in stat:
            assert self.overlay_index < len(self.viewport.overlays)
            overlay = self.viewport.overlays[self.overlay_index]
            if overlay.pipeline is None:
                stat = stat.replace("<pipeline>", "None")
            else:
                pipeline_id = find_key_from_value(pipeline_map, overlay.pipeline)
                stat = stat.replace(
                    "<pipeline>", f"pipeline{format_pipeline_id(pipeline_id)}"
                )
        self.overlay_index += "overlays" in stat
        return stat


def write_imports(stream: io.StringIO, include_vis: bool):
    stream.write(
        "# Boilerplate code generated by OVITO Pro {}\n".format(ovito.version_string)
    )
    stream.write("from ovito.io import *\n")
    stream.write("from ovito.modifiers import *\n")
    stream.write("from ovito.data import *\n")
    stream.write("from ovito.pipeline import *\n")
    if include_vis:
        stream.write("from ovito.vis import *\n")
        stream.write("from ovito.qt_compat import QtCore\n")


def create_pipeline(
    stream: io.StringIO, pipeline: Pipeline, include_vis: bool, pipeline_id: int
):
    global pipeline_map
    assert pipeline_id not in pipeline_map
    pipeline_map[pipeline_id] = pipeline
    # Generate call to import_file() creating the Pipeline object.
    pipeline_source = pipeline.source
    if isinstance(pipeline_source, ovito.pipeline.FileSource):
        stream.write("\n\n# Data import:\n")
        # Ask the pipeline's FileSource to compile the list of arguments to be passed to the
        # import_file() function.
        filesource_attrs = {}
        pipeline_source.__codegen__(filesource_attrs)
        # Note: FileSource.__codegen__() would normally generate a call to the FileSource.load() method.
        # Here we just take the call argument list and use it to generate a call to import_file() instead.
        if "load" in filesource_attrs:
            stream.write(
                f"pipeline{format_pipeline_id(pipeline_id)} = import_file{filesource_attrs['load'][0]}"
            )
        else:
            stream.write(
                f"pipeline{format_pipeline_id(pipeline_id)} = Pipeline(source=FileSource())\n"
            )  # Instantiate an empty FileSource if the external file path hasn't been set.

        # Generate a user-defined modifier function that sets up the data objects in the input
        # data collection of the pipeline. This is needed to replay the manual changes the user has made to these objects in the GUI.
        if hasattr(pipeline_source, "data") and pipeline_source.data:
            has_data_object_setup = False
            data = pipeline_source.data
            for dataobj in data._get_all_objects_recursive():
                dataobj_props = get_object_modified_properties(stream, None, dataobj)
                if not dataobj_props:
                    continue

                prefix = find_object_prefix_recursive(data, dataobj, make_mutable=True)
                if prefix is None:
                    continue

                for attr_name in sorted(dataobj_props.keys()):
                    attr_diff = dataobj_props[attr_name]
                    for diff in attr_diff:
                        if not has_data_object_setup:
                            has_data_object_setup = True
                            stream.write(
                                "\n\n# Manual modifications of the imported data objects:"
                            )
                            stream.write(
                                "\ndef modify_pipeline_input(frame: int, data: DataCollection):"
                            )
                        stream.write(f"\n    data{prefix}.{attr_name}{diff}")
            if has_data_object_setup:
                stream.write(
                    f"\npipeline{format_pipeline_id(pipeline_id)}.modifiers.append(modify_pipeline_input)"
                )

    elif isinstance(pipeline_source, ovito.pipeline.PythonSource):
        if pipeline_source.delegate is not None:
            # Unless it is a predefined Python source included with OVITO Pro, copy the original source
            # code into the generated script.
            if not type(pipeline_source.delegate).__module__.startswith(
                "ovito._extensions.scripts."
            ):
                if len(pipeline_source.script) != 0:
                    stream.write("\n\n# Source code of user-defined pipeline source:\n")
                    stream.write(pipeline_source.script)
                else:
                    # Generate an import statement for the module the class is defined in.
                    stream.write(
                        f"\nfrom {type(pipeline_source.delegate).__module__} import *"
                    )

            stream.write(f"\n\n# {pipeline_source.title}:\n")

            # Create a default-initialized source instance.
            # It will be used to detect which parameters were modified by the user.
            default_source = type(pipeline_source.delegate)()
            statements = generate_object_instantiation(
                stream, "src", default_source, pipeline_source.delegate, include_vis
            )
            if isinstance(statements, str):
                # Generate in-place class instantiation:
                source_statements = f"pipeline{format_pipeline_id(pipeline_id)} = Pipeline(source=PythonSource(delegate={statements}))"
            else:
                # Generate code with a temporary variable holding the source object.
                assignments = [
                    statement
                    for statement in statements
                    if is_property_assignment(statement)
                ]
                method_calls = [
                    statement
                    for statement in statements
                    if not is_property_assignment(statement)
                ]
                all_statements = (
                    assignments
                    + [
                        f"pipeline{format_pipeline_id(pipeline_id)} = Pipeline(source=PythonSource(delegate=src))"
                    ]
                    + method_calls
                )
                source_statements = "\n".join(all_statements)
            stream.write(source_statements)
        else:
            # Output the script source code entered by the user.
            stream.write("\n\n# User-defined pipeline source function:\n")
            stream.write(pipeline_source.script)
            if not pipeline_source.kwargs:
                stream.write(
                    "\n# Create a data pipeline with a script-based source object:"
                )
                stream.write(
                    f"\npipeline{format_pipeline_id(pipeline_id)} = Pipeline(source = PythonSource(function = create))"
                )
            else:
                # Pass the values of the user-defined parameters to the script function using
                # partial function parameter binding.
                stream.write("\nimport functools")
                kwargs_list = []
                for key, value in pipeline_source.kwargs.items():
                    if isinstance(value, RefTarget):
                        statements = generate_object_instantiation(
                            stream,
                            key,
                            type(value)(),
                            value,
                            include_vis,
                            prefer_oneliner=True,
                        )
                    else:
                        statements = format_property_value(value)
                    if isinstance(statements, str):
                        # Generate in-place instantiation:
                        kwargs_list.append("{} = {}".format(key, statements))
                    else:
                        # Generate code with a temporary variable:
                        stream.write("\n" + "\n".join(statements))
                        kwargs_list.append("{} = {}".format(key, key))

                if len(kwargs_list) > 2:
                    kwargs_list = ["\n    " + arg for arg in kwargs_list]

                stream.write(
                    "\n# Create a data pipeline with a Python-based source object:"
                )
                stream.write(
                    f"\npipeline{format_pipeline_id(pipeline_id)} = Pipeline(source = PythonSource(function = functools.partial(create, {', '.join(kwargs_list)})))"
                )
    else:
        stream.write(
            "\n# The currently selected data pipeline '{}' has a data source of type {}.\n# This program version is not able to generate code for this pipeline source type.".format(
                pipeline.object_title, type(pipeline_source)
            )
        )


def find_replaced_visual_element_prefix(pipeline: Pipeline, vis: DataVis):
    # find_visual_element_prefix returns none, if it is called with a replacement visual element.
    # Therefore we need to use the original visual element, taken from replaced_vis_elements to
    # find the prefix.
    # returns None if the prefix could not be determined
    prefix = find_visual_element_prefix(pipeline, vis, use_pipeline_output=True)
    if prefix:
        return prefix

    for rep_vis in pipeline.replaced_vis_elements:
        if pipeline.get_replacement_vis_element(rep_vis) is not vis:
            continue
        prefix = find_visual_element_prefix(pipeline, rep_vis, use_pipeline_output=True)
        if prefix:
            return prefix
    return None


def write_visual_elements_first_pass(
    stream: io.StringIO, pipeline: Pipeline, pipeline_id: int
):
    has_header = False
    for vis in pipeline.vis_elements:
        prefix = find_replaced_visual_element_prefix(pipeline, vis)
        if prefix is None:
            continue

        if vis not in pipeline.replacement_vis_elements:
            continue

        if not has_header:
            has_header = True
            stream.write("\n\n# Generate independent visual elements for pipeline")
        stream.write(
            f"\npipeline{format_pipeline_id(pipeline_id)}.make_vis_element_independent(pipeline{format_pipeline_id(pipeline_id)}.compute(){prefix})"
        )


def format_prefix_to_identifier(prefix: str) -> str:
    prefix = (
        prefix.lstrip(".").replace(r"['", "_").replace(r"']", "_").replace(".", "_")
    )
    while " " in prefix:
        prefix = prefix.replace(" ", "-")
    while "-" in prefix:
        prefix = prefix.replace("-", "_")
    while "__" in prefix:
        prefix = prefix.replace("__", "_")
    assert prefix.isidentifier(), prefix
    return prefix


def write_visual_elements_second_pass(
    stream: io.StringIO,
    pipeline: Pipeline,
    pipeline_id: int,
    data_already_written: set[str],
):
    has_header = False
    for vis_count, vis in enumerate(pipeline.vis_elements):
        prefix = find_replaced_visual_element_prefix(pipeline, vis)
        if prefix is None:
            continue

        vis_props = get_object_modified_properties(stream, None, vis, True)
        replaced = vis in pipeline.replacement_vis_elements
        has_variable = False
        for attr_name, attr_diff in vis_props.items():
            for diff in attr_diff:
                # skip root data.vis modification if it was already written
                if (
                    f"{prefix}.{attr_name}{diff}" in data_already_written
                    and not replaced
                ):
                    continue
                if not has_header:
                    has_header = True
                    stream.write("\n\n# Configure visual elements for pipeline")
                if replaced:
                    if not has_variable:
                        has_variable = True
                        if vis_count > 0:
                            stream.write("\n")
                        stream.write(
                            f"\n{format_prefix_to_identifier(prefix)} = pipeline{format_pipeline_id(pipeline_id)}.get_replacement_vis_element(pipeline{format_pipeline_id(pipeline_id)}.compute(){prefix})"
                        )
                    stream.write(
                        f"\n{format_prefix_to_identifier(prefix)}.{attr_name}{diff}"
                    )
                else:
                    stream.write(
                        f"\npipeline{format_pipeline_id(pipeline_id)}.compute(){prefix}.{attr_name}{diff}"
                    )
                    data_already_written.add(f"{prefix}.{attr_name}{diff}")


def write_visual_elements(stream: io.StringIO, pipeline_breakpoints: list[int]):
    # cache previously written data.vis modifications
    data_already_written: set[str] = set()

    stream.write("\n\n# ======= Set up visual elements ======= #")

    # duplicate required visual elements
    for pipeline_id in sorted(pipeline_map.keys()):
        write_visual_elements_first_pass(
            stream,
            pipeline_map[pipeline_id],
            pipeline_id,
        )

    # configure all visual elements
    for pipeline_id in sorted(pipeline_map.keys()):
        if pipeline_id in pipeline_breakpoints:
            data_already_written = set()
        write_visual_elements_second_pass(
            stream,
            pipeline_map[pipeline_id],
            pipeline_id,
            data_already_written,
        )

    # write transformations for the pipeline
    for pipeline_id in sorted(pipeline_map.keys()):
        codegen_pipeline_transformation(
            stream, pipeline_map[pipeline_id], None, pipeline_id
        )

    # add pipeline(s) to scene
    stream.write("\n\n# Add pipelines to scene")
    for pipeline_id in sorted(pipeline_map.keys()):
        stream.write(f"\npipeline{format_pipeline_id(pipeline_id)}.add_to_scene()")


def branch_pipeline(
    stream: io.StringIO,
    pipeline_ids: Sequence[int],
):
    global pipeline_map
    assert len(pipeline_ids) >= 2
    for pipeline_id in range(1, len(pipeline_ids)):
        assert pipeline_ids[pipeline_id] in pipeline_map
        stream.write(
            f"\n\n# Branch pipeline {format_pipeline_id(pipeline_ids[pipeline_id])} off pipeline {format_pipeline_id(pipeline_ids[0])}"
        )
        stream.write(
            f"\npipeline{format_pipeline_id(pipeline_ids[pipeline_id])} = Pipeline(head=pipeline{format_pipeline_id(pipeline_ids[0])}.head)"
        )


def write_modifier(
    stream: io.StringIO,
    node: Node,
    include_vis: bool,
    pipeline_id: int,
    modifier_name: Optional[str],
):
    assert not isinstance(node, InputNode)
    if isinstance(node, EndNode):
        return

    # Generate statements for creating the modifiers in the pipeline.
    modifier = node.modifier

    # Skip hidden modifier types which are not documented.
    if not modifier.__doc__:
        stream.write(f"\n\n# Skipping modifier '{modifier.object_title}'")
        return

    codegen_modifier(
        stream, modifier, include_vis, node.group, pipeline_id, modifier_name
    )


def reuse_modifier(
    stream: io.StringIO,
    group: Any,
    pipeline_id: int,
    modifier_title: str,
    modifier_name: str,
):
    stream.write(f"\n\n# Add pre-defined {modifier_title} modifier to pipeline")
    indent = ""
    if group is not None and group.enabled is False:
        stream.write(f"\n# Skipping disabled modifier '{modifier_title}'")
        stream.write("\nif False:")
        indent = "    "
    stream.write(
        f"\n{indent}pipeline{format_pipeline_id(pipeline_id)}.modifiers.append({modifier_name})"
    )


def update_pipeline_map(pipelines: list[Pipeline]):
    global pipeline_map
    # TODO; This performs badly
    for pipeline in pipelines:
        if pipeline not in pipeline_map.values():
            pipeline_map[max(pipeline_map.keys()) + 1] = pipeline


def create_modifier_chain(
    stream: io.StringIO,
    network: Network,
    start: int,
    sc: deque | int,
    shared_modifiers: SharedModifiers,
    include_vis: bool,
):
    if not isinstance(sc, deque):
        sc = deque((sc,))
    node = network[start]
    if isinstance(node, ModificationNode) and node.shared is not None:
        if id(node.shared) not in shared_modifiers:
            mod_name = shared_modifiers.get_name(node)
            shared_modifiers[id(node.shared)] = mod_name
            write_modifier(stream, node.node, include_vis, sc[0], mod_name)
        reuse_modifier(
            stream, node.node.group, sc[0], str(node), shared_modifiers[id(node.shared)]
        )
    elif isinstance(node, ModificationNode):
        write_modifier(stream, node.node, include_vis, sc[0], None)

    if len(node.children) != 1:
        sc.extend([i + sc[-1] + 1 for i in range(len(node.children) - 1)])
        update_pipeline_map(node.pipelines)
        branch_pipeline(stream, sc)
    if len(node.children) == 1 and node.children[0] is None:
        pipeline_id = sc[-1] if len(sc) > 0 else pipeline_id
        sc.popleft()
    for child in node.children:
        if child is not None:
            pipeline_id = create_modifier_chain(
                stream, network, child, sc, shared_modifiers, include_vis
            )
    return pipeline_id


def codegen_pipeline_visibility(
    stream,
    pipeline_map: dict[int, Pipeline],
    vp: Viewport,
    include_parents: bool = True,
):
    """Generates Python statements for pipeline visibility in viewport."""
    has_header = False

    def write_header():
        nonlocal has_header, stream
        if not has_header:
            header = "\n\n# Pipeline visibility in viewport"
            stream.write(header)
            has_header = True

    for pipeline_id in sorted(pipeline_map.keys()):
        pipeline = pipeline_map[pipeline_id]
        if pipeline.is_hidden_in_viewport(vp, include_parents):
            # write_header() # Header is probably unnecessary
            stream.write(f"\npipeline{format_pipeline_id(pipeline_id)}.set_viewport_visibility(vp, False)")


def codegen_scene(include_vis: bool) -> str:

    global pipeline_map
    pipeline_map = {}

    """Generates Python statements for setting up a data pipeline."""
    # get the global scene
    scene = ovito.scene

    # Generate script header.
    stream = io.StringIO()
    write_imports(stream, include_vis)

    # Generate pipeline tree
    network = Network()
    for pipe in scene.pipelines:
        network.add_pipeline(pipe)

    # modifiers shared between pipelines
    shared_modifiers = SharedModifiers()

    # Find modifiers required for overlays
    if include_vis:
        viewports_first_pass(scene, network, shared_modifiers)

    # pipeline_index
    pipeline_ids = [-1]

    stream.write("\n\n# ==== Set up pipeline ==== #")

    # Loop over all unique pipeline heads
    for node in network.get_pipeline_roots():
        # Create the source for the pipeline
        pipeline_ids[-1] += 1
        create_pipeline(
            stream, network[node].pipeline, include_vis, pipeline_id=pipeline_ids[-1]
        )
        # Build chain of modification nodes in the pipeline.
        pipeline_ids.append(
            create_modifier_chain(
                stream, network, node, pipeline_ids[-1], shared_modifiers, include_vis
            )
        )
    pipeline_ids = pipeline_ids[:-1]

    # Generate statements for modification of pipeline playback rates
    for pipeline_id in sorted(pipeline_map.keys()):
        codegen_trajectory_playback(
            stream, pipeline_map[pipeline_id], None, pipeline_id
        )

    # Generate statements for modification of visual elements.
    if include_vis:
        write_visual_elements(stream, pipeline_ids)

    # Generate statements for setting up the viewport and viewport layout.
    if include_vis and ovito.scene.viewports.active_vp:

        stream.write("\n\n# ========== Set up rendering ========== #")

        # Generate statement for creating and configuring the Viewport instance(s).
        stream.write("\n\n# Viewport setup:")
        rs = ovito.scene.render_settings
        if not rs.render_all_viewports:
            # Rendering just the active viewport.
            formatter = ViewportStatementFormatter(
                ovito.scene.viewports.active_vp, shared_modifiers
            )
            for stat in property_value_diff(
                stream,
                None,
                ovito.scene.viewports.active_vp,
                True,
                force_instantiation=True,
            ):
                stream.write(f"\nvp{formatter(stat)}")
                codegen_pipeline_visibility(
                    stream, pipeline_map, ovito.scene.viewports.active_vp
                )
        else:
            # Rendering a viewport layout.
            stream.write("\nviewport_layout = []")
            for vp_rect in ovito.scene.viewports.get_viewport_rectangles():
                formatter = ViewportStatementFormatter(vp_rect[0], shared_modifiers)
                stream.write(f'\n\n# Viewport "{vp_rect[0].title}":')
                for stat in property_value_diff(
                    stream,
                    None,
                    vp_rect[0],
                    True,
                    force_instantiation=True,
                ):
                    stream.write(f"\nvp{formatter(stat)}")
                stream.write(
                    f"\nviewport_layout.append((vp, {vp_rect[1]!r}))  # [left,top,width,height]"
                )
                codegen_pipeline_visibility(stream, pipeline_map, vp_rect[0])

        # Generate statement for setting up the renderer.
        statements = property_value_diff(
            stream, None, rs.renderer, True, force_instantiation=True
        )
        has_renderer = False
        if len(statements) > 1 or statements[0] != " = OpenGLRenderer()":
            has_renderer = True
            stream.write("\n\n# Renderer setup:")
            for stat in statements:
                stream.write(f"\nrenderer{stat}")

        # Generate call to render_image() or render_anim().
        stream.write("\n\n# Rendering:\n")
        args = []
        args.append(f"size={rs.size!r}")
        if (rs.background_color != 1.0).any():
            args.append(f"background={format_property_value(rs.background_color)}")
        if has_renderer:
            args.append("renderer=renderer")
        if rs.render_all_viewports:
            args.append("layout=viewport_layout")
        if rs.range == RenderSettings.Range.CurrentFrame:
            args.insert(
                0,
                "filename={!r}".format(
                    rs.output_filename if rs.output_filename else "image.png"
                ),
            )
            if rs.generate_alpha:
                args.append("alpha=True")
            if ovito.scene.anim.current_frame != 0:
                args.append(f"frame={ovito.scene.anim.current_frame}")
            stream.write("vp.render_image({})".format(", ".join(args)))
        else:
            args.insert(
                0,
                "filename={!r}".format(
                    rs.output_filename if rs.output_filename else "movie.mp4"
                ),
            )
            args.append(f"fps={ovito.scene.anim.frames_per_second!r}")
            if rs.range == RenderSettings.Range.CustomInterval:
                args.append("range={!r}".format(rs.custom_range))
            if rs.every_nth_frame > 1:
                args.append(f"every_nth={rs.every_nth_frame!r}")
            stream.write(f"vp.render_anim({', '.join(args)})")

    src = stream.getvalue()
    stream.close()
    return src


if __name__ == "__main__":
    from ovito.io import *  # noqa: F403
    from ovito.modifiers import *  # noqa: F403
    from ovito.vis import *  # noqa: F403
    from ovito.pipeline import *  # noqa: F403
#    print(codegen_pipeline(ovito.scene.selected_pipeline, True))
