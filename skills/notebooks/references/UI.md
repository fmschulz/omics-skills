marimo has a rich set of UI components. 

* `mo.ui.altair_chart(chart)` - create a reactive Altair chart
* `mo.ui.button(on_click=None, value=None, kind='neutral', *, label='click here')` - create a clickable button (`kind`: neutral, success, warn, danger)
* `mo.ui.run_button(kind='neutral', tooltip=None, *, label='click to run')` - create a button that runs code
* `mo.ui.checkbox(value=False, *, label='')` - create a checkbox
* `mo.ui.chat(model, *, prompts=None)` - create a chat interface; `model` is a callable `(messages, config)` that returns the reply
* `mo.ui.date(start=None, stop=None, value=None, *, label='', full_width=False)` - create a date picker
* `mo.ui.dropdown(options, value=None, allow_select_none=None, searchable=False, *, label='', full_width=False)` - create a dropdown menu
* `mo.ui.file(filetypes=None, multiple=False, kind='button', *, label='')` - create a file upload element (`kind`: button, area)
* `mo.ui.number(start=None, stop=None, step=None, value=None, *, label='', full_width=False)` - create a number input
* `mo.ui.radio(options, value=None, inline=False, *, label='')` - create radio buttons
* `mo.ui.refresh(options=None, default_interval=None, *, label='')` - create a refresh control, for example `options=['1s', '5s'], default_interval='1s'`
* `mo.ui.slider(start, stop, step=None, value=None, *, label='', full_width=False)` - create a slider
* `mo.ui.range_slider(start, stop, step=None, value=None, *, label='', full_width=False)` - create a range slider; `value` is `[low, high]`
* `mo.ui.table(data, pagination=None, selection='multi', page_size=None, *, label='')` - create an interactive table with built-in search and sort; read the selected rows from `.value`
* `mo.ui.text(value='', placeholder='', kind='text', *, label='', full_width=False)` - create a text input
* `mo.ui.text_area(value='', placeholder='', *, label='', full_width=False)` - create a multi-line text input
* `mo.ui.data_explorer(df)` - create an interactive dataframe explorer
* `mo.ui.dataframe(df)` - display a dataframe with search, filter, and sort capabilities
* `mo.ui.plotly(figure)` - create a reactive Plotly chart (supports scatter, treemap, and sunburst)
* `mo.ui.tabs(tabs, value=None)` - create a tabbed interface from a dictionary of tab name to content
* `mo.ui.array(elements)` - create an array of UI elements from a list
* `mo.ui.form(element, *, bordered=True, label='')` - wrap an element in a form

Inspect the installed API with `uv run --no-project --with marimo python -c "import marimo as mo; help(mo.ui.form)"`.

## Forms

You can compose multiple UI elements into a single form using `.batch().form()`. The `.batch()` method binds named UI elements into a markdown template, and `.form()` adds a submit button so values are only sent on submit.

```python
form = (
    mo.md(
        """
        **Choose an option**

        {choice}

        **Enter some text**

        {text}

        **Enable feature**

        {flag}
        """
    )
    .batch(
        choice=mo.ui.dropdown(options=["A", "B", "C"]),
        text=mo.ui.text(),
        flag=mo.ui.checkbox(),
    )
    .form(
        submit_button_label="Submit",
        show_clear_button=True,   # optional
        clear_on_submit=False,    # keep values after submit
    )
)

form
```

You can also add validation to a form using the `validate` parameter. Return an error string to block submission, or `None` to allow it.

```python
group_by_form = mo.ui.dropdown(
    options=df_columns,
    label="Select column to filter for duplicate analyzis",
    allow_select_none=True,
    value=None,  # start with nothing selected
    searchable=True,
).form(
    submit_button_label="Apply",
    validate=lambda v: (
        "Please select a column and press Apply."
        if v is None else None
    ),
)
```

However, the user may also want to use other components. Popular alternatives include the `ScatterWidget` from the `drawdata` library, `moutils`, and `wigglystuff`. 

For custom classes and static HTML representations you can also use the `_display_` method. 

```python
class Dice:
    def _display_(self):
        import random

        return f"You rolled {random.randint(0, 7)}"
```
