"""This Module contains the TemporaryResources context manager

The purpose of the TemporaryResources context manager is to enable using temporary, specific
configuration of resources when creating a custom Template.

If you use the global configuration `pn.config` for your templates you will include the same
css and js files in all templates. This is problematic if you want different templates, like for
example a light template, a dark template, a bootstrap template, a material template, a template
with Plotly Plots, and template without Plotly plots etc."""
from typing import Callable, Dict, List, Optional, Set

import panel as pn
from bokeh.model import Model

EXTENSIONS = {**pn.extension._imports}  # pylint: disable=protected-access


class TemporaryResources:  # pylint: disable=(too-many-instance-attributes
    """The purpose of the TemporaryResources context manager is to enable using temporary, specific
    configuration of resources when creating a custom Template.

    If you use the global configuration `pn.config` for your templates you will include the same
    css and js files in all templates. This is problematic if you want different templates, like for
    example a light template, a dark template, a bootstrap template, a material template, a template
    with Plotly Plots, and template without Plotly plots etc."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        extensions: Optional[Set] = None,
        raw_css: Optional[List] = None,
        css_files: Optional[List] = None,
        js_files: Optional[Dict] = None,
        include_panel_css: bool = True,
    ):
        """The purpose of the `TemporaryResources` context manager is to enable using temporary,
        specific configuration of resources when creating a custom Template.

        If you use the global configuration `pn.config` for your templates you will include the same
        css and js files in all templates. This is problematic if you want different templates,
        like for example a light template, a dark template, a bootstrap template, a material
        template, a template with Plotly Plots, and template without Plotly plots etc.

        Args:
            extensions (Optional[Set], optional): Custom pn.extensions like. For example {'plotly'}.
                Defaults to None.
            raw_css (Optional[List], optional): Corresponds to pn.config.raw_css.
                Defaults to None.
            css_files (Optional[List], optional): Corresponds to pn.config.css_files.
                Defaults to None.
            js_files (Optional[Dict], optional): Corresponds to pn.js_files. Defaults to None.
            include_panel_css (bool, optional): If False the Panel css is not included. You can use
                this if you wan't to create static pages without Panel functionality. The page will
                load quicker if the Panel css is not included, Defaults to True.

        >>> pn.config.raw_css = ["body {color: black}"]
        >>> with TemporaryResources(raw_css=["body {color: white}"]):
        ...     temporary_raw_css = pn.config.raw_css
        ...     temporary_header = pn.io.resources.Resources().render()
        >>> temporary_raw_css
        ['body {color: white}']
        >>> pn.config.raw_css
        ['body {color: black}']
        >>> "body {color: white}" in temporary_header
        True
        >>> "body {color: black}" in temporary_header
        False

        Please note that the `pn.io.resources.Resources().render` function is what is normally
        used by Bokeh and Panel to render the resources (css+js) in the head of the template. Thus
        by using the TemporaryResources context manager we can get specific resources in the head
        of the template only."""
        super().__init__()

        self._extensions = extensions or set()
        self._raw_css = raw_css or []
        self._css_files = css_files or []
        self._js_files = js_files or {}
        self._include_panel_css = include_panel_css

        self._backup_raw_css = pn.config.raw_css
        self._backup_css_files = pn.config.css_files
        self._backup_js_files = pn.config.js_files
        self._backup_model_class_reverse_map = Model.model_class_reverse_map

    def __enter__(self):
        if self._extensions:
            pn.extension(*self._extensions)

        pn.config.raw_css = self._raw_css
        pn.config.js_files = self._js_files
        pn.config.css_files = [*self._panel_css_files, *self._css_files]
        exclude_extension = self._get_exclude_extension_func(self._extensions)
        Model.model_class_reverse_map = {
            name: model
            for name, model in self._backup_model_class_reverse_map.items()
            if not exclude_extension(name)
        }

    def __exit__(self, type, value, traceback):  # pylint: disable=redefined-builtin
        Model.model_class_reverse_map = self._backup_model_class_reverse_map
        pn.config.css_files = self._backup_css_files
        pn.config.js_files = self._backup_js_files
        pn.config.raw_css = self._backup_raw_css

    @property
    def _panel_css_files(self) -> List[str]:
        return [
            file
            for file in self._backup_css_files
            if self._is_panel_style_file(file) and self._include_panel_css
        ]

    @staticmethod
    def _is_panel_style_file(file: str) -> bool:
        if "panel\\_styles" in file:
            return True
        if "panel/_styles" in file:
            return True
        return False

    @staticmethod
    def _get_exclude_extension_func(extensions: Optional[Set] = None) -> Callable:
        """Returns a function that can determine whether the given model/ extension
        should be included in the temporary list of models/ extensions.

        Args:
            extensions (Optional[Set], optional): [description]. Defaults to None.

        Returns:
            Callable: [description]
        """
        if extensions is None:
            extensions = set()
        extensions_to_exclude = [v for k, v in EXTENSIONS.items() if k not in extensions]

        def exclude_extension(model: str) -> bool:
            """Returns whether the given model/ extension
            should be included in the temporary list of models/ extensions.

            I.e. if the model is a Bokeh extension (like Panels DeckGl extension) that is not in
            the specified extensions. Then it should not be included.

            Args:
                model (str): Name of a (module of a) model. For example 'panel.models.deckgl'.

            Returns:
                bool: True if the model should be included. False otherwise.
            """
            model_str = model
            if not "." in model_str or "bokeh." in model_str:
                return False
            for extension in extensions_to_exclude:
                if extension in model_str:
                    return True
            return False

        return exclude_extension
