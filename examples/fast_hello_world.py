from panel_components.component import make_tag_function
from panel_components.tags import script, div, h1
import holoviews as hv
hv.extension('bokeh')

fast_design_system_provider = make_tag_function("fast-design-system-provider")
fast_button = make_tag_function("fast-button")
fast_card = make_tag_function("fast-card")

data = [('one',8),('two', 10), ('three', 16), ('four', 8), ('five', 4), ('six', 1)]
bars = hv.Bars(data, hv.Dimension('Car occupants'), 'Count')

def fast(*children, **attributes):
    module = script(
        type="module",
        src="https://unpkg.com/@microsoft/fast-components",
    )
    provider = fast_design_system_provider(
        *children,
        use_defaults=True,
        style="min-height:100vh;",
        **attributes,
    )
    fast_template = div(
        module,
        provider,
        main="",
    )
    fast_template._panel_raw_css["fast-template"]="body {margin: 0px}"
    fast_template._src_folder="panel_components\\www" # Needed in order to get assets copied
    return fast_template

layout = fast(
    div(
        fast_card(
            h1("A Card"),
            fast_button("Click Me", appearance="accent"),
            bars,
            style="width:300px;height:500px;margin:20px"
        ),

    )
)

if __name__.startswith("bokeh"):
    layout.servable()
elif __name__=="__main__":
    layout.servable().show(port=5007)