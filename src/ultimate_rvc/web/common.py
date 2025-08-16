"""
Module defining common utility functions and classes for the
web application of the Ultimate RVC project.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Concatenate, ParamSpec, TypeVar

from functools import partial

import gradio as gr

from ultimate_rvc.core.exceptions import NotProvidedError
from ultimate_rvc.core.manage.config import load_config, save_config
from ultimate_rvc.web.config.main import TotalConfig
from ultimate_rvc.web.typing_extra import SongTransferOption, SpeechTransferOption

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from gradio.components import Component
    from gradio.events import Dependency

    from ultimate_rvc.web.config.component import AudioConfig
    from ultimate_rvc.web.typing_extra import (
        BaseDropdownChoices,
        BaseDropdownValue,
        ComponentVisibilityKwArgs,
        DropdownChoices,
        DropdownValue,
        TextBoxKwArgs,
        UpdateAudioKwArgs,
        UpdateDropdownKwArgs,
    )

PROGRESS_BAR = gr.Progress()

T = TypeVar("T")
P = ParamSpec("P")
U = TypeVar("U", bound=SongTransferOption | SpeechTransferOption)


def exception_harness(  # noqa: UP047
    fn: Callable[P, T],
    info_msg: str | None = None,
) -> Callable[P, T]:
    """
    Wrap a function in a harness that catches exceptions and re-raises
    them as instances of `gradio.Error`.

    Parameters
    ----------
    fn : Callable[P, T]
        The function to wrap.

    info_msg : str, optional
        Message to display in an info-box pop-up after the function
        executes successfully.

    Returns
    -------
    Callable[P, T]
        The wrapped function.

    """

    def _wrapped_fn(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            res = fn(*args, **kwargs)
        except gr.Error:
            raise
        except NotProvidedError as e:
            msg = e.ui_msg or e
            raise gr.Error(str(msg)) from None
        except Exception as e:
            raise gr.Error(str(e)) from e
        else:
            if info_msg:
                gr.Success(info_msg, duration=1)
            return res

    return _wrapped_fn


def confirmation_harness(  # noqa: UP047
    fn: Callable[P, T],
) -> Callable[Concatenate[bool, P], T]:
    """
    Wrap a function in a harness that requires a confirmation before
    executing and catches exceptions, re-raising them as instances of
    `gradio.Error`.

    Parameters
    ----------
    fn : Callable[P, T]
        The function to wrap.

    Returns
    -------
    Callable[Concatenate[bool, P], T]
        The wrapped function.

    """

    def _wrapped_fn(confirm: bool, *args: P.args, **kwargs: P.kwargs) -> T:
        if confirm:
            return exception_harness(fn)(*args, **kwargs)
        err_msg = "Confirmation missing!"
        raise gr.Error(err_msg)

    return _wrapped_fn


def render_msg(
    template: str,
    *args: str,
    display_info: bool = False,
    **kwargs: str,
) -> str:
    """
    Render a message template with the provided arguments.

    Parameters
    ----------
    template : str
        Message template to render.
    args : str
        Positional arguments to pass to the template.
    display_info : bool, default=False
        Whether to display the rendered message as an info message
        in addition to returning it.
    kwargs : str
        Keyword arguments to pass to the template.

    Returns
    -------
    str
        Rendered message.

    """
    msg = template.format(*args, **kwargs)
    if display_info:
        gr.Info(msg)
    return msg


def confirm_box_js(msg: str) -> str:
    """
    Generate a JavaScript code snippet which:
      * defines an anonymous function that takes one named parameter and
      zero or more unnamed parameters
      * renders a confirmation box
      * returns the choice selected by the user in that confirmation
      box in addition to any unnamed parameters passed to the function.

    Parameters
    ----------
    msg : str
        Message to display in the confirmation box rendered by the
        JavaScript code snippet.

    Returns
    -------
    str
        The JavaScript code snippet.

    """
    return f"(x, ...args) => [confirm('{msg}'), ...args]"


def update_value(x: str | None) -> dict[str, Any]:
    """
    Update the value of a component.

    Parameters
    ----------
    x : str | None
        New value for the component.

    Returns
    -------
    dict[str, Any]
        Dictionary which updates the value of the component.

    """
    return gr.update(value=x)


def update_values(*xs: str) -> tuple[dict[str, Any], ...]:
    """
    Update the values of multiple components.

    Parameters
    ----------
    xs : str
        New values for the components.

    Returns
    -------
    tuple[dict[str, Any], ...]
        Tuple of dictionaries which update the values of the components.

    """
    return tuple(gr.update(value=x) for x in xs)


def toggle_visibility(
    value: T,
    targets: set[T],
    default: str | float | None = None,
    update_default: bool = False,
) -> dict[str, Any]:
    """
    Toggle the visibility of a component based on equality of
    a value and one of a set of targets.

    Parameters
    ----------
    value : T
        The value to compare against the target.
    targets : set[T]
        The set of targets to compare the value against.
    default : str | float | None, optional
        Default value for the component.
    update_default : bool, default=False
        Whether to update the default value of the component.

    Returns
    -------
    dict[str, Any]
        Dictionary which updates the visibility of the component.

    """
    update_args: ComponentVisibilityKwArgs = {"visible": value in targets}
    if update_default:
        update_args["value"] = default
    return gr.update(**update_args)


def toggle_visibilities(
    num_components: int,
    value: T,
    targets: set[T],
    defaults: Sequence[str | float | None] = [],
    update_default: bool = False,
) -> list[dict[str, Any]]:
    """
    Toggle the visibility of multiple components based on equality of
    a value and one of a set of targets.

    Parameters
    ----------
    num_components : int
        Number of components to set visibility for.
    value : T
        The value to compare against the target.
    targets : set[T]
        The set of targets to compare the value against.
    defaults : Sequence[str | float | None], optional
        Default values for the components.
    update_default : bool, default=False
        whether to update the default values of the components.

    Returns
    -------
    list[dict[str, Any]]
        List of dictionaries which update the visibility of the
        components.

    Raises
    ------
    ValueError
        If the number of default values does not match the number of
        components.

    """
    if update_default and len(defaults) != num_components:
        err_msg = "Number of default values must be equal to the number of components."
        raise ValueError(err_msg)
    update_args_list: list[ComponentVisibilityKwArgs] = []
    for index in range(num_components):
        update_args: ComponentVisibilityKwArgs = {"visible": value in targets}
        if update_default:
            update_args["value"] = defaults[index]
        update_args_list.append(update_args)
    return [gr.update(**update_args) for update_args in update_args_list]


def toggle_visible_component(
    num_components: int,
    visible_index: int,
    reset_values: bool = True,
) -> dict[str, Any] | tuple[dict[str, Any], ...]:
    """
    Reveal a single component from a set of components. All other
    components are hidden.

    Parameters
    ----------
    num_components : int
        Number of components to set visibility for.
    visible_index : int
        Index of the component to reveal.
    reset_values : bool, default=True
        Whether to reset the values of the components.

    Returns
    -------
    dict[str, Any] | tuple[dict[str, Any], ...]
        A single dictionary or a tuple of dictionaries that update the
        visibility of the components.

    Raises
    ------
    ValueError
        If the visible index exceeds or is equal to the number of
        components to set visibility for.

    """
    if visible_index >= num_components:
        err_msg = (
            "Visible index must be less than the number of components to set visibility"
            " for."
        )
        raise ValueError(err_msg)
    update_args_list: list[ComponentVisibilityKwArgs] = []
    for _ in range(num_components):
        update_args: ComponentVisibilityKwArgs = {"visible": False}
        if reset_values:
            update_args["value"] = None
        update_args_list.append(update_args)
    update_args_list[visible_index]["visible"] = True
    match update_args_list:
        case [update_args]:
            return gr.update(**update_args)
        case _:
            return tuple(gr.update(**update_args) for update_args in update_args_list)


def initialize_dropdowns(
    fn: Callable[P, BaseDropdownChoices],
    num_components: int,
    value: BaseDropdownValue = None,
    value_indices: Sequence[int] = [],
    *args: P.args,
    **kwargs: P.kwargs,
) -> list[gr.Dropdown]:
    """
    Initialize the choices and optionally the value of one or more
    dropdown components.


    Parameters
    ----------
    fn : Callable[P, BaseDropdownChoices]
        Function to get initial choices for the dropdown components.
    num_components : int
        Number of dropdown components to initialize.
    value : BaseDropdownValue, optional
        New value for dropdown components.
    value_indices : Sequence[int], default=[]
        Indices of dropdown components to initialize the value for.
    args : P.args
        Positional arguments to pass to the function used to initialize
        dropdown choices.
    kwargs : P.kwargs
        Keyword arguments to pass to the function used to initialize
        dropdown choices.

    Returns
    -------
    list[gr.Dropdown]
        List of initialized dropdown components.

    Raises
    ------
    ValueError
        If not all provided indices are unique or if an index exceeds
        or is equal to the number of dropdown components.

    """
    if len(value_indices) != len(set(value_indices)):
        err_msg = "Value indices must be unique."
        raise ValueError(err_msg)
    if value_indices and max(value_indices) >= num_components:
        err_msg = (
            "Index of a dropdown component to update the value for exceeds the number"
            " of dropdown components to update."
        )
        raise ValueError(err_msg)
    updated_choices = fn(*args, **kwargs)
    if value is None or value not in updated_choices:
        value = next(iter(updated_choices), None)
        if isinstance(value, tuple):
            value = value[1]
    update_args_list: list[UpdateDropdownKwArgs] = [
        {"choices": updated_choices} for _ in range(num_components)
    ]
    for index in value_indices:
        update_args_list[index]["value"] = value
    return [gr.Dropdown(**update_args) for update_args in update_args_list]


def update_dropdowns(
    fn: Callable[P, DropdownChoices],
    num_components: int,
    value: DropdownValue = None,
    value_indices: Sequence[int] = [],
    *args: P.args,
    **kwargs: P.kwargs,
) -> gr.Dropdown | tuple[gr.Dropdown, ...]:
    """
    Update the choices and optionally the value of one or more dropdown
    components.

    Parameters
    ----------
    fn : Callable[P, DropdownChoices]
        Function to get updated choices for the dropdown components.
    num_components : int
        Number of dropdown components to update.
    value : DropdownValue, optional
        New value for dropdown components.
    value_indices : Sequence[int], default=[]
        Indices of dropdown components to update the value for.
    args : P.args
        Positional arguments to pass to the function used to update
        dropdown choices.
    kwargs : P.kwargs
        Keyword arguments to pass to the function used to update
        dropdown choices.

    Returns
    -------
    gr.Dropdown | tuple[gr.Dropdown,...]
        Updated dropdown component or components.

    Raises
    ------
    ValueError
        If not all provided indices are unique or if an index exceeds
        or is equal to the number of dropdown components.

    """
    if len(value_indices) != len(set(value_indices)):
        err_msg = "Value indices must be unique."
        raise ValueError(err_msg)
    if value_indices and max(value_indices) >= num_components:
        err_msg = (
            "Index of a dropdown component to update the value for exceeds the number"
            " of dropdown components to update."
        )
        raise ValueError(err_msg)
    updated_choices = fn(*args, **kwargs)
    update_args_list: list[UpdateDropdownKwArgs] = [
        {"choices": updated_choices} for _ in range(num_components)
    ]
    for index in value_indices:
        update_args_list[index]["value"] = value

    match update_args_list:
        case [update_args]:
            # NOTE This is a workaround as gradio does not support
            # singleton tuples for components.
            return gr.Dropdown(**update_args)
        case _:
            return tuple(gr.Dropdown(**update_args) for update_args in update_args_list)


def toggle_intermediate_audio(visible: bool, num_components: int) -> list[gr.Accordion]:
    """
    Toggle the visibility of intermediate audio accordions.

    Parameters
    ----------
    visible : bool
        Visibility status of the intermediate audio accordions.

    num_components : int
        Number of intermediate audio accordions to toggle visibility
        for.

    Returns
    -------
    list[gr.Accordion]
        The intermediate audio accordions.

    """
    accordions = [gr.Accordion(open=False) for _ in range(num_components)]
    return [gr.Accordion(visible=visible, open=False), *accordions]


def update_output_name(
    fn: Callable[P, str],
    update_placeholder: bool = False,
    *args: P.args,
    **kwargs: P.kwargs,
) -> gr.Textbox:
    """
    Update a textbox component so that it displays a suitable name for
    an output audio file.

    Parameters
    ----------
    fn : Callable[..., str]
        Function to generate the output name.
    update_placeholder : bool, default=False
        Whether to update the placeholder text instead of the value of
        the textbox component.
    args : P.args
        Positional arguments to pass to the function used to generate
        the output name.
    kwargs : P.kwargs
        Keyword arguments to pass to the function used to generate the
        output name.

    Returns
    -------
    gr.Textbox
        Textbox component with updated value or placeholder text.

    """
    update_args: TextBoxKwArgs = {}
    update_key = "placeholder" if update_placeholder else "value"
    if (args and any(args)) or (kwargs and any(kwargs)):
        output_name = fn(*args, **kwargs)
        update_args[update_key] = output_name
    else:
        update_args[update_key] = None
    return gr.Textbox(**update_args)


def update_audio(
    num_components: int,
    output_indices: Sequence[int],
    track: str | None,
    disallow_none: bool = True,
) -> gr.Audio | tuple[gr.Audio, ...]:
    """
    Update the value of a subset of `Audio` components to the given
    audio track.

    Parameters
    ----------
    num_components : int
        The total number of `Audio` components under consideration.
    output_indices : Sequence[int]
        Indices of `Audio` components to update the value for.
    track : str
        Path pointing to an audio track to update the value of the
        indexed `Audio` components with.
    disallow_none : bool, default=True
        Whether to disallow the value of the indexed components to be
        `None`.

    Returns
    -------
    gr.Audio | tuple[gr.Audio, ...]
        Each `Audio` component under consideration with the value of the
        indexed components updated to the given audio track.

    """
    update_args_list: list[UpdateAudioKwArgs] = [{} for _ in range(num_components)]
    for index in output_indices:
        if track or not disallow_none:
            update_args_list[index]["value"] = track
    match update_args_list:
        case [update_args]:
            return gr.Audio(**update_args)
        case _:
            return tuple(gr.Audio(**update_args) for update_args in update_args_list)


def render_transfer_component(
    value: list[U],
    label_prefix: str,
    option_type: type[U],
) -> gr.Dropdown:
    """
    Render a dropdown for transferring tracks.

    Parameters
    ----------
    value : list[U]
        The default selected values for the dropdown.
    label_prefix : str
        The prefix for the dropdown label.
    option_type : type[U]
        The type of the transfer options.

    Returns
    -------
    gr.Dropdown
        A dropdown component for transferring tracks.

    """
    return gr.Dropdown(
        choices=list(option_type),
        label=f"{label_prefix} destination",
        info=(
            "Select the input track(s) to transfer the"
            f" {label_prefix.lower()} to when the 'Transfer"
            f" {label_prefix.lower()}' button is clicked."
        ),
        type="index",
        multiselect=True,
        value=value,
    )


def setup_transfer_event(
    btn: gr.Button,
    transfer: gr.Dropdown,
    output: gr.Audio,
    input_configs: Sequence[AudioConfig],
) -> Dependency:
    """
    Set up a transfer track event for a button component.


    Parameters
    ----------
    btn : gr.Button
        The button to set up the event for.
    transfer : gr.Dropdown
        A dropdown component containing transfer options.
    output : gr.Audio
        An audio component containing the track to transfer.
    input_configs : Sequence[AudioConfig]
        A sequence of configurations for all input audio components
        that can be transferred to.

    Returns
    -------
    Dependency
        The event listener for the button click.


    """
    return btn.click(
        partial(update_audio, len(input_configs)),
        inputs=[transfer, output],
        outputs=[c.instance for c in input_configs],
        show_progress="hidden",
    )


def setup_delete_event(
    button: gr.Button,
    fn: Callable[..., None],
    inputs: list[Component],
    outputs: gr.Textbox,
    confirm_msg: str,
    success_msg: str,
) -> Dependency:
    """
    Set up a delete event for a button component.

    Parameters
    ----------
    button : gr.Button
        Button component to set up the delete event for.
    fn : Callable[..., None]
        Function to call when the button is clicked.
    inputs : list[Component]
        List of input components to pass to the function that is called
        when the button is clicked.
    outputs : gr.Textbox
        Textbox component to update with a success message upon
        successful deletion.
    confirm_msg : str
        Message to display in a confirmation box before executing the
        delete event.
    success_msg : str
        Message to display in the provided textbox component upon
        successful deletion.


    Returns
    -------
    Dependency
        A dependency that can be used for sequencing the delete
        event with other events.

    """
    return button.click(
        confirmation_harness(fn),
        inputs=inputs,
        outputs=outputs,
        js=confirm_box_js(confirm_msg),
    ).success(partial(render_msg, success_msg), outputs=outputs, show_progress="hidden")


def save_total_config_values(name: str, *values: *tuple[Any, ...]) -> None:
    """
    Save the provided component values to a total configuration model
    and write it to a JSON file with the provided name.

    Parameters
    ----------
    name : str
        The name of the JSON file to write the total configuration model
        to.
    *values : *tuple[Any, ...]
        The component values to save to the total configuration model.

    """
    new_config = TotalConfig()
    for value, component_config in zip(values, new_config.all, strict=True):
        component_config.value = value

    save_config(name, new_config)


def load_total_config_values(name: str) -> tuple[Any, ...]:
    """
    Load a total configuration model from a JSON file with the provided
    name and return the non-excluded values of its nested component
    configurations.


    Parameters
    ----------
    name : str
        The name of the JSON file to load the total configuration model
        from.

    Returns
    -------
    tuple[Any, ...]
        The non-excluded values of the nested component configurations
        in the loaded total configuration model.

    """
    new_config = load_config(name, TotalConfig)
    return tuple(c.value for c in new_config.all)
