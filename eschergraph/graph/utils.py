from __future__ import annotations

import builtins
import re
from ast import Expression
from ast import parse
from ast import Subscript
from typing import Any
from typing import Callable
from typing import TypeVar

from attrs import fields

from eschergraph.exceptions import DataLoadingException
from eschergraph.graph.base import EscherBase
from eschergraph.graph.community import Community as Community
from eschergraph.graph.loading import LoadState
from eschergraph.graph.persistence.metadata import Metadata as Metadata
# Custom graph atttribute classes need to be imported for discovery for creating getters and setters

T = TypeVar("T", bound=EscherBase)


def loading_getter_setter(cls: type[T]) -> type[T]:
  """A function that programmatically writes the getter and setters for an Escher base class.

  This decorator can be added to any class to reduce the boilerplate code that is needed to
  setup the property getter and setter for the lazily loaded attributes in the loading groups.

  Args:
    cls (EscherBase): The EscherBase class to add the getter and setter methods to.

  Returns:
    The same class with the getter and setter methods added (with type annotations).
  """
  for attr in fields(cls):
    # Only add the getter / setter if the attribute is in a loading group
    if "group" in attr.metadata:
      if attr.metadata["group"] == LoadState.REFERENCE:
        continue

      def make_getter(attr_name: str, type_hint: str) -> Callable[[Any], Any]:
        class_type: type = _parse_future_annotations(type_hint)

        def getter(self: Any) -> Any:
          self._check_loadstate(attr_name=attr_name)
          if not isinstance(getattr(self, attr_name), class_type):
            raise DataLoadingException(
              f"The {attr_name} attribute has not been loaded."
            )

          return getattr(self, attr_name)

        # Add type annotations to the getter function (self is not part of the annotation)
        getter.__annotations__ = {"return": _extract_property_type(type_hint)}

        return getter

      def make_setter(attr_name: str, type_hint: str) -> Callable[[Any, Any], None]:
        class_type: type = _parse_future_annotations(type_hint)

        def setter(self: Any, value: Any) -> None:
          self._check_loadstate(attr_name=attr_name)

          if not isinstance(getattr(self, attr_name), class_type):
            raise DataLoadingException(
              f"The {attr_name} attribute has not been loaded."
            )

          setattr(self, attr_name, value)

        # Add type hinting to the setter method
        setter.__annotations__ = {
          "return": "None",
          "value": _extract_property_type(type_hint),
        }

        return setter

      prop: property = property(
        make_getter(attr_name=attr.name, type_hint=attr.type),
        make_setter(attr_name=attr.name, type_hint=attr.type),
      )
      property_name: str = attr.name[1:]
      setattr(cls, property_name, prop)

  return cls


def _parse_future_annotations(annotation: str) -> type:
  """Parse the string nested Optional annotation into a type.

  The type can be used for isinstance checks on the Node object
  when dealing with loading states.

  Args:
    annotation (str): The Optional[...] annotation for which the first inner class has to be extracted.

  Returns:
    The first nested class as a type (an uninstantiated class).
  """
  class_name: str = _extract_inner_type(annotation)
  # Return if it is a class in the global scope
  class_type: Any | None = globals().get(class_name)
  # Otherwise check for a builtin class
  if not class_type:
    class_type = getattr(builtins, class_name, None)

  if class_type and isinstance(class_type, type):
    return class_type  # type: ignore
  else:
    raise RuntimeError()


def _extract_inner_type(annotation: str) -> str:
  """Extract the string type annotation of the first class within a potentially nested Optional[....] type annotation.

  Args:
    annotation (str): Type annotation that contains a type within an optional.

  Returns:
    The first string in the optional block.
  """
  if not annotation or "Optional" not in annotation:
    return ""

  parsed_annotation: Expression = parse(annotation, mode="eval")
  # Extract the inner type
  inner_type: Any = parsed_annotation.body.slice  # type: ignore
  if hasattr(inner_type, "value"):
    inner_type = inner_type.value
  if isinstance(inner_type, Subscript):
    return str(inner_type.value.id)  # type: ignore
  return str(inner_type.id)


def _extract_property_type(annotation: str) -> str:
  """Extract the type of the property variable that is within the Optional[...] string type annotation.

  Args:
    annotation (str): The String annotation.

  Returns:
    The string annotation of the non-optional property value.
  """
  match = re.match(r"Optional\[(.*)\]", annotation)
  if match:
    return match.group(1)
  return ""
