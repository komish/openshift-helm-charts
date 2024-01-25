# -*- coding: utf-8 -*-
"""Utilities for working with chart fixtures."""

from string import Template
from os import getcwd
from e2e_templates import hc_minimal_chart_yaml


def write_chart_yaml(
        name: str
    ) -> str:
    """Writes a Chart.yaml with the provided inputs.
    
    This will write exactly in the working directory.
    Navigate to the correct receiving directory, or use a context
    manager such as SetDirectory to write this file to the right place.

    Always overwrites.

    Returns:
        The full path of the Chart.yaml that was written.
    """

    contents = Template(hc_minimal_chart_yaml).substitute({'chart_name': name})
    with open('Chart.yaml', 'w') as f:
        f.write(contents)
        
    return getcwd() + '/Chart.yaml'
    