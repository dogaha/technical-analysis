import time
import re
from datetime import date, datetime, timedelta
from pywinauto import Application  
from pywinauto.timings import Timings
import utils

# ---------------------------------------------------------
# SPEED OPTIMIZATION: Reduce pywinauto's default internal delays
# ---------------------------------------------------------
logger = utils.get_logger()

Timings.fast()

app = Application(backend="uia").connect(title="Historical Data")
dlg = app.window(title="Historical Data")


# Export Section
export_tab = dlg.child_window(auto_id="HistoricalDataWindowExportExpander",control_type="Group")
if export_tab.get_expand_state() == 0:
    export_tab.expand()

contract_selector = dlg.child_window(auto_id="cbxInsSelExport",control_type="ComboBox")
start_date_selector = dlg.child_window(auto_id="HistoricalDataWindowExportStartDateSelector",control_type="Edit")
end_date_selector = dlg.child_window(auto_id="HistoricalDataWindowExportEndDateSelector",control_type="Edit")
interval_selector = dlg.child_window(auto_id="HistoricalDataWindowExportIntervalSelector",control_type="ComboBox")
data_selector = dlg.child_window(auto_id="HistoricalDataWindowExportDataTypeSelector",control_type="ComboBox")
export_button = dlg.child_window(auto_id="MarketDataArchivesWindowExportButton", control_type="Button")

print("Finished Referencing Export Elements")

start_year = 2024
end_year = 2025

contract_selector.click_input()
time.sleep(1)
contract_selector.click_input()

interval_selector.select("Minute")
data_selector.select("Last")

contract_items = contract_selector.descendants(control_type="ListItem")
contracts_to_export = []
for i in contract_items:
    contract = i.window_text()

    # Is ES
    if not contract.startswith('ES'):
        continue

    # Is within year range
    match = re.search(r'\d{2}$', contract)
    if match:
        number = match.group()
        if start_year <= 2000+int(number) <= end_year:
            contracts_to_export.append(contract)

#landingPath = r"/opt/airflow/data/landing/"
landingPath = "F:\\Projects\\Personal\\technical-analysis\\es-pipeline\\data\\landing\\"
# landingPath = "G:\\MarketData\\Raw\\ES\\"

print("Finished Prep")

for contract in contracts_to_export:
    try:
        print(f"Start Export of  {contract}")

        clean_contract = contract.replace(" ", "")
        match = re.match(r'^([A-Z]{2})([A-Z]{3})(\d{2})$', clean_contract)
        if not match:
            raise Exception(f"{clean_contract} is not a valid es contract") # Handle invalid contract formats safely
            
        root, month, year = match.groups()
    
        month_code = utils.EXPIRY_MONTH_STR_EZ.get(month, "UNKNOWN") 
        if month_code=="UNKNOWN":
            raise Exception(f"{month} is not a valid month")
        
        c = root+month_code+year
        s,e = utils.get_daterange(c)
        year, month, day = str(s).split("-")
        s = f"{month}/{day}/{year}"
        year, month, day = str(e).split("-")
        e = f"{month}/{day}/{year}"
        #print("Finished Date Calcs")

        contract_selector.select(contract)
        #print("Finished Selecting Contract")

        start_date_selector.set_text(s)
        #print("Finished Selecting Start Date")

        end_date_selector.set_text(e)
        #print("Finished Selecting End Date")

        export_button.click()
        #print("Finished Clicking Button")

        save_window = dlg.child_window(title="Save",control_type="Window")
        #save_window.wait("exists visible enabled ready", timeout=2)
        #print("Finished Getting Save Window")

        file_name_entry = save_window.child_window(title="File name:", control_type="Edit")
        file_name_entry.type_keys(landingPath + c)
        file_name_entry.type_keys("{ENTER}")
        #print("Finished Setting File Name")
        
        #save_button = save_window.child_window(auto_id="1", control_type="Button")
        #save_button.click()
        #print("Finished Saving File")

        confirmation_window = dlg.child_window(title="Description",control_type="Window")
        confirmation_window.wait("exists visible enabled ready", timeout=5)
        #print("Finished Getting Confirmation Window")

        confirmation_button = confirmation_window.child_window(auto_id="NTMessageBoxOKButton",control_type="Button")
        confirmation_button.click()
        #print("Finished Confiriming")

    except Exception as e:
        print(f"Error processing {contract}: {e}")

print("Finshed Running Script")





