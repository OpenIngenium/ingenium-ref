'''
This is reference Ingenium Custom Script it intended as a demo of the capabilities in a custom script
 and as a template to follow for implementation.


Authors:
    * Chris Swan 
    * Hongman Kim 

'''


import time
from datetime import datetime, timedelta
import copy
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import random
from ing_lib.logs import init_console_logger, get_logger
from ing_lib.steps import (
    get_input_output_paths,
    read_input_file,
    write_output_file,
    write_series_file,
)
from pathlib import Path
import string
init_console_logger()
logger = get_logger(__name__)

GRAPH_FILE_NAME = 'sample_graph.png'
GRAPH_FILE_NAME_2 = 'sample_graph2.png'
FILE_NAME_1 = 'sample_file.txt'
FILE_NAME_2 = 'sample_file_2.txt'


def random_text(num_chars: int) -> str:
    # You can tailor the charset; here we include letters, digits, punctuation, space
    charset = string.ascii_letters + string.digits + string.punctuation + " "
    return ''.join(random.choice(charset) for _ in range(num_chars))

def plot_series(series: dict, output_dir: str, png_name: str):
    """
    Plot **all** channel time‑series on a single figure and save as PNG.

        {
            "series_output": {
                "timetype": "Earth Return Time",
                "series": [
                    {"name": "...",
                     "color": "#RRGGBB",
                     "series_type": "HORIZONTAL" | "VERTICAL",
                     "data": [(timestamp:str, value), ...]},
                    …
                ],
            }
        }

    """

    # ------------------------------------------------------------------
    #   Helper – parse timestamps (same helper used elsewhere in this file)
    # ------------------------------------------------------------------
    def _parse_timestamp(ts):
        """Return a ``datetime`` or ``None``."""
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, (int,float)):
            return ts
        try:
            ts_str = str(ts).strip().rstrip('Z')
            return datetime.strptime(ts_str, "%Y-%jT%H:%M:%S.%f")
        except Exception as exc:
            logger.error(f"Could not parse timestamp '{ts}': {exc}")
            return None


    if not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    #   Create figure & axis – **use plt.subplots**, not plt.subplot
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(12, 6))

    # X‑axis label
    timetype = series.get("timetype", "Time")
    ax.set_xlabel(timetype)

    x_is_time_type = False
    plotted_any = False   # <-- will stay False if no channel has valid points

  # ------------------------------------------------------------------
    #   Iterate over every series entry
    # ------------------------------------------------------------------
    for s in series.get("series", []):
        name = s.get("name", "")
        series_type = s.get("series_type", "HORIZONTAL").upper()
        colour = s.get("color", "#000000")
        data = s.get("data", [])

        # --------------------------------------------------------------
        #   VERTICAL series – draw a single dashed line per point
        # --------------------------------------------------------------
        if series_type == "VERTICAL":
            for ts_raw, label in data:
                x = _parse_timestamp(ts_raw)
                if x is None:
                    continue
                
                if isinstance(x, datetime):
                    x_is_time_type = True

                # Draw the vertical dashed line
                ax.axvline(x=x, color=colour, linestyle="--", linewidth=1.0)

                # Position the label near the top of the plot (95% of ymax)
                ylim = ax.get_ylim()
                y_label = ylim[1] * 0.95
                ax.text(x, y_label, str(label),
                        rotation=90,
                        ha="right",
                        va="top",
                        fontsize=8,
                        color=colour)

            continue   # Skip generic line handling for this series

        # --------------------------------------------------------------
        #   HORIZONTAL series – plot (time, value) line
        # --------------------------------------------------------------
        timestamps = []
        values = []
        for ts_raw, val in data:
            x = _parse_timestamp(ts_raw)
            if x is None:
                continue
            timestamps.append(x)

            if isinstance(x,datetime):
                x_is_time_type = True

            try:
                values.append(float(val))
            except Exception:
                logger.debug(f"Could not convert value '{val}' for series '{name}'. Skipping.")
                # If conversion fails, the point is omitted

        if not timestamps:
            logger.warning(f"No valid points for series '{name}'. Skipping plot.")
            continue

        ax.plot(timestamps, values,
                color=colour,
                linewidth=2,
                marker='o',
                markersize=4,
                label=name)
        plotted_any = True   # At least one horizontal line was drawn

    # ------------------------------------------------------------------
    #   Finalise the figure
    # ------------------------------------------------------------------
    if plotted_any:
        ax.set_title(f"Telemetry – DN vs. {timetype}")
        ax.grid(True, which="both", ls="--", lw=0.5, alpha=0.7)
        ax.legend(loc="best", fontsize="small")
        

        if x_is_time_type:
            ax.xaxis_date()
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%jT%H:%M:%S.%f"))
            fig.autofmt_xdate()
        else:
            import matplotlib.ticker as mticker
            ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))
    else:
        # No data – create a placeholder figure
        ax.set_title("No valid telemetry data to display")
        ax.axis("off")
        plt.axis('off')  # hide axes
    
    plt.tight_layout()

    # ------------------------------------------------------------------
    #   Save the PNG
    # ------------------------------------------------------------------
    png_path = os.path.join(output_dir, png_name)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)

    logger.info(f"Saved combined telemetry plot → {png_path}")

if __name__ == '__main__':


    # Locate the custom script input file
    error_msg = 'USAGE: python reference_step.py input_file_path output_file_path'
    input_file_abs_path, output_file_abs_path = get_input_output_paths(error_msg)
    logger.info(f'input_file_abs_path: {input_file_abs_path}')
    logger.info(f'output_file_abs_path: {output_file_abs_path}')

    # Read the input file
    logger.info('Reading custom script inputs')
    input_dict = read_input_file(input_file_abs_path)

    # Initialize the Output Data
    '''
    Users should construct the output data structure as a python dictionary and initialize the status to "PENDING"
    Later the script will update this dictionary as results are produced and it can be easily saved to the outputs.json
    
    Note that this varies per script (as the outputs vary)
    '''


    # Initialize output data
    inputs = copy.deepcopy(input_dict.get('inputs', []))
    variables = input_dict.get('variables', {})
    telemetry= copy.deepcopy(variables.get('telemetry', {}))
    parameters=copy.deepcopy(variables.get('parameters', {}))    
    entries = copy.deepcopy(input_dict.get('entries', {}))
    outputs = {
        'start_time_date_time': '',
        'query_start': '',
        'query_end': '',
        'file_output_1': FILE_NAME_1,
        'file_output_2': FILE_NAME_2,
        'image_output_1': GRAPH_FILE_NAME,
        'image_output_2': GRAPH_FILE_NAME_2
    }
    my_output_array = []

    output_dict = {
        'custom_script_status': 'PENDING',
        'inputs': inputs,
        'entries': entries,
        'outputs': outputs,
        'output_array': my_output_array,
        'output_summary': ''
    }

    # Step through each entry and initialize the outputs
    for i, entry in enumerate(entries):
        entry['verification_status'] = 'PENDING'
        entry['entry_outputs'] = {
            'entry_output_1': 0,   # INT
            'entry_output_2': 0.0, # FLOAT
            'entry_output_3': 0,   # INT
            'entry_output_4': 0.0, # FLOAT
            'entry_output_5': 0.0, # FLOAT
            'entry_output_6': 0,   # INT
        }
        entry['entry_output_array'] = []

    # Write initial output
    write_output_file(output_dict, output_file_abs_path)
    logger.info('Output file was initialized')

    '''
    Add the custom script logic here
    Remember to:
        - Program defensibly (use try/except, think about what happens if actions fail)
        - Update the output_dict as you go and save it when new results are available (this will provide visibility while it is executing)
        - Log the actions - it helps with visibility and troubleshooting
        - Remember that the script will likley be running as an application user - not as you
    '''

    '''
    The following code builds random ouputs for the script
    '''

    # Convert the start_time to a datetime object
    start_time = datetime.strptime(inputs['start_time'], '%Y-%jT%H:%M:%S')
    
    # Compute the query range
    query_start = start_time - timedelta(seconds=inputs['lookback'])
    query_end = start_time + timedelta(seconds=inputs['timeout'])
    
    # Update the query range in the outputs
    outputs['start_time_date_time'] = start_time.strftime('%Y-%jT%H:%M:%S.%f')
    outputs['query_start'] = query_start.strftime('%Y-%jT%H:%M:%S.%f')
    outputs['query_end'] = query_end.strftime('%Y-%jT%H:%M:%S.%f')

    # Populate output values
    for i, entry in enumerate(entries):
        entry['verification_status'] = 'PASS'
        entry['entry_outputs']['entry_output_1'] = '' + str(i)
        entry['entry_outputs']['entry_output_2'] = '' + str(10*i)

        entry_output_array = entry['entry_output_array']
        for j in range(random.randint(2,6)):
            elem = {
                'entry_output_array_field_1': '' + str(j),
                'entry_output_array_field_2': '' + str(10*j),
            }
            entry_output_array.append(elem)
        
        write_output_file(output_dict, output_file_abs_path)
        logger.info(f'Entry was added: {i}')


    # Populate my_output_array (top‑level) with the defined fields
    for i in range(random.randint(2,15)):
        item = {
            'output_array_field_1': i,               # INT
            'output_array_field_2': float(10 * i),   # FLOAT
            'output_array_field_3': float(20 * i),   # FLOAT
            'output_array_field_4': i * 2,           # INT
            'output_array_field_5': i * 3,           # INT
            'output_array_field_6': float(30 * i),   # FLOAT
            'output_array_field_7': i * 4,           # INT
        }
        my_output_array.append(item)

    # Build a series
    series = {}
    series['series_output_1'] = {'timetype': 'SCLK',
                                'series': [
                                            {
                                            'name': 'Voltage (V)',
                                            'series_type': 'HORIZONTAL',
                                            'color': '#499894',
                                            'data': []
                                            },
                                            {
                                            'name': 'Temperature (C)',
                                            'series_type': 'HORIZONTAL',
                                            'color': '#FF0000',
                                            'data': []
                                            }

                                        ]
                                }
    start_time_seconds = start_time.timestamp()

    for s in series['series_output_1']['series']:
        for i in range(random.randint(8,20)):
            time = start_time_seconds + i*random.uniform(1,10)
            value = random.randrange(3,14)
            s['data'].append((time,value))

      
        s['data'].sort(key=lambda pt:pt[0])

    event_time_1 = start_time_seconds + i*random.uniform(1,10)
    event_time_2 = event_time_1 + i * random.uniform(1, 10)

    event = {
            'name': 'Event',
            'series_type': 'VERTICAL',
            'color': '#FF0000',
            'data': []
            }
    event['data'].append((event_time_1,"TURN_ON"))
    event['data'].append((event_time_2, "TURN_OFF"))

    series['series_output_1']['series'].append(event)

    series['series_output_2'] ={'timetype': 'SCET',
                                  'series': [
                                      {
                                          'name': 'CMD_CNT',
                                          'series_type': 'HORIZONTAL',
                                          'color': "#101111",
                                          'data': []
                                      },
                                      {
                                          'name': 'CMD_REJECTED',
                                          'series_type': 'HORIZONTAL',
                                          'color': "#00FFAA",
                                          'data': []
                                      },
                                      {
                                          'name': 'CMD_COMPLETED',
                                          'series_type': 'HORIZONTAL',
                                          'color': "#FFA034",
                                          'data': []
                                      }

                                  ]
                              }

    for s in series['series_output_2']['series']:
        for i in range(random.randint(8,20)):
            time = start_time + timedelta(seconds=i*random.randint(1,10))
            value = random.randrange(3,14)
            s['data'].append((time.strftime('%Y-%jT%H:%M:%S.%f'),value))

        s['data'].sort(key=lambda pt: datetime.strptime(pt[0], '%Y-%jT%H:%M:%S.%f'))

    event_time_1 = start_time + timedelta(seconds=i*random.randint(1,10))

    event = {
        'name': 'Event',
        'series_type': 'VERTICAL',
        'color': "#3700FF",
        'data': []
    }
    event['data'].append((event_time_1.strftime('%Y-%jT%H:%M:%S.%f'),"BAD_COMMAND"))

    series['series_output_2']['series'].append(event)

    '''
    If your script has entries - evaluate them to determine overall status.
    '''
    # Review entries to generate overall status
    custom_script_status = 'PASS'
    for entry in entries:
        if entry['verification_status'] != 'PASS':
            custom_script_status = 'FAIL'
            break

    '''
    Log the successful completion and Push the final status (PASS/FAIL/ERROR) to the output_dict - 
    Ingenium watches for the status to be Not equal to PENDING 
    
    Note that you will likely have some logic to determine pass/fail (or will base it off entry verification_status)
    '''
    msg = f'reference_step.py has run to completion with overall status: {custom_script_status}'
    logger.info(msg)
    output_dict['custom_script_status'] = custom_script_status

    '''
    Build a text compatible representation of the step output.
    Ingenium steps are complicated JSON objects which don't translate well into reporting tools like Excel.
    
    Custom Scripts should produce a text compatible translation of the step contents for use in these situations.
    (obviously this can not include things like images/series/etc.)
    '''

    text_representation = f'Sending Flight CMD: {output_dict["inputs"]["flight_cmd"].split(",")[0]} and Sim CMD: {output_dict["inputs"]["sim_cmd"].split(",")[0]} at {output_dict["inputs"]["start_time"]}\n'
    for entry in entries:
        text_representation = text_representation + f'Querying Flight Channel:{entry["entry_inputs"]["flight_channel"].split(",")[0]} Sim Channel:{entry["entry_inputs"]["sim_channel"].split(",")[0]} (EVRs:{entry["entry_inputs"]["flight_evr"]}, {entry["entry_inputs"]["sim_evr"]}) - Value:{entry["entry_outputs"]["entry_output_1"]}\n'

    text_representation = text_representation + f'Generated: {output_dict["outputs"]["file_output_1"]},{output_dict["outputs"]["file_output_1"]}'

    output_dict['output_summary'] = text_representation

    # Write any series or image data
    output_dir = os.path.dirname(output_file_abs_path)
    write_series_file(series,output_dir)

    # Write image of channels graphed
    plot_series(series['series_output_1'], output_dir, GRAPH_FILE_NAME)
    plot_series(series['series_output_2'], output_dir, GRAPH_FILE_NAME_2)

    # Write Files
    output_path = Path(os.path.join(output_dir, FILE_NAME_1))
    output_path.write_text(random_text(10000), encoding="utf-8")
    output_path = Path(os.path.join(output_dir, FILE_NAME_2))
    output_path.write_text(random_text(10000), encoding="utf-8")
    # Report Final custom_script_status
    write_output_file(output_dict, output_file_abs_path)

