'''
Program to take an Excel input file and generate Artisan help dialog code.

Command line:  xlsx_to_artisan_help.py [<filename>]
**Note that filename should have no suffix.  File name only.

Input file is always drawn from ../input_files/<filename>.xlsx
If filename is not specified 'test' will be used.

Output is always written to ../output_files/<filename>.py
    which will be executed and writes to ../output_files/<filename>.html
    and to ../output_files/help.html.
    The help.html file is useful when working with several different Excel files and
    need to only hit refresh in the browser instead of loading a new file.

Excel file format:
    One Excel file for each help dialog.
    One or more tabs, each tab is a seperate table within the same help dialog.
    The tab name is not important but it will be used to generate the associated PrettyTable table name.

    Each tab must have the following cells, starting in the upper left cell A1
    Title of the table               [First row, required]
    Top Note                         [Multiple contiguous rows, optional]
    Table headers, aka column titles [One row, optional but if provided must include table rows]
    Table data rows                  [Multiple coniguous rows, optional but must follow the table headers]
    Bottom Note                      [Multiple contiguous rows, optional]

    QApplication.translate() is not applied to cells formatted as Italic, formatted with any font color 
    or if the cell has a numeric value.
    
    Beware: Single quotes in cells will be replaced with double quotes.
    
    Single blank rows are legal. Consecutive blank rows are interpreted as the end of a table. All cells in 
    a blank row must be empty.
 
    Top Notes: Can be one or more contiguous rows that will be combined in a single block.  Each row starts a new line.
               New lines can be embedded into the notes text.  '\n' without the quotes.
               Each row must begin with one of 'topnote:' or 'tn:' without the quotes, case insensitive.

    Bottom Notes: Can be one or more contiguous rows that will be combined in a single block.  Each row starts a new line.
                  New lines can be embedded into the notes text.  '\n' without the quotes.
                  Each row must begin with one of 'botnote:' or 'bn:' or 'bottomnote:' without the quotes, case insensitive.
    There is no error checking for notes position so if top and bottom notes are reversed bad things will happen.

Known problems:
-The unicode elipsis \x85 "…" is not properly handled.  These seem to get into the Excel file when cut and paste from the blog.
Must be replaced with three periods "..." in the Excel file.  

- openpyxl does not always report the correct last row or column. This will be seen when rendering the HTML.  This is reported
as not fixable. If this happens, go back to the source Excel file and manually delete the excess rows or columns manually.
https://stackoverflow.com/questions/46569496/openpyxl-max-row-and-max-column-wrongly-reports-a-larger-figure#46571480
A hack was added to correct for openpyxl reporting too many rows. There is not a hack for columns at this time.

'''

from os.path import join, dirname, abspath
import subprocess
import sys
import re
from PyQt5.QtWidgets import QApplication
from openpyxl import load_workbook
import prettytable

def u(x):
    return str(x)
    
ind = "        "     #indent
nlind = "\n" + ind   #new line plus indent

def translateStr(str, group='HelpDlg'):
    t_str = "u(QApplication.translate('" + group + "','" + u(str) + "',None))"
    return t_str

def generateRows(ws):
    all_rows = []
    for row in ws.iter_rows():
        this_row = []
        for cell in row:
            # insert a nonbreaking space into blank cells to keep the row height homgenous
            if cell.value == None or cell.value == '':
                cell_str = "'&#160;'"
            else:
                if cell.data_type == 's': 
                    cell_value = re.subn(r"'",r'"',cell.value)  #protect downstream by changing single quotes to double 
                    # do not translate if the cell has italic format or any font color
                    if cell.font.italic or \
                            (cell.font.color != None and \
                             type(cell.font.color.rgb) == str and \
                             cell.font.color.rgb != "FF000000"):    
                        cell_str = "'" + cell_value[0] + "'"           
                    else:
                        cell_str = translateStr(cell_value[0])
                else:
                    # numeric value
                    cell_str = str(cell.value)
            
            this_row.append(cell_str)
        all_rows.append(this_row)
    return all_rows

def getTitle(all_rows,ws,nsheet):
    if nsheet == 0:
        title = nlind + 'helpstr += "<b>" + ' + str(all_rows[0][0]) + ' + "</b>"'
    else:
        title = nlind + 'helpstr += "<br/><br/><b>" + ' + str(all_rows[0][0]) + ' + "</b>"'
    return title
  
def getNotes(all_rows,nrows,tbl_name,notetype='top'):
    tbl_name = tbl_name + notetype
    tbl_notes = ""
    notes = []
    notes_len = 0
    for idx in range(1, nrows):
        if notetype == 'top':
            gotnote = re.subn(r'topnote:|tn:','',str(all_rows[idx][0]),0,re.IGNORECASE)
        else:
            gotnote = re.subn(r'botnote:|bn:|bottomnote:','',str(all_rows[idx][0]),0,re.IGNORECASE)
        if gotnote[1]:
            notes.append(gotnote[0])
            notes_len += 1
    notes = '+newline+'.join(notes)
    tbl_notes += nlind + tbl_name + ' = prettytable.PrettyTable()'
    tbl_notes += nlind + tbl_name + '.header = False'
    tbl_notes += nlind + tbl_name + '.add_row([' + notes + '])'

    return tbl_notes, notes_len

def getFieldnames(rows,tbl_name):
    this_row = ','.join(rows)
    field_names = u(tbl_name) + ".field_names = [" + str(this_row) + "]"
    return field_names
    
def getAddrows(all_rows,tbl_name):
    addrows = ""
    tbl = ""
    for idx in range(len(all_rows)):
        this_row = ','.join(all_rows[idx])
        if idx > 0:
            addrows += nlind
        addrows += u(tbl_name) + ".add_row([" + this_row + "])"
    return addrows

def buildpyCode(fname_in,fname_out_html):

    data_table_attributes = '"width":"100%","border":"1","padding":"1","border-collapse":"collapse"'
    note_table_attributes = '"width":"100%","border":"1","padding":"1","border-collapse":"collapse"'

    outstr = ""
    
    # wrap the output with python code to allow it to execute
    outstr += '\n' + 'import prettytable'
    outstr += '\n' + 'import re'
    outstr += '\n' + 'from PyQt5.QtWidgets import QApplication'
    outstr += '\n' + 'def u(x):'
    outstr += '\n' + '    return str(x)'
    outstr += '\n' + 'if True:  #here just to achieve the indent'
    outstr += '\n' + '    if True:'
    outstr += '\n# ----- Cut below ---------------------------------------------'
    
    # initialize the output string
    outstr += '\n'
    outstr += nlind + '# autogenerated help pasted below'
    outstr += '\n'
    outstr += nlind + 'newline = "\\n"  #@UnusedVariable'
    outstr += nlind + 'helpstr = ""'
    outstr += nlind + 'helpstr += "<head><style>"'
    outstr += nlind + 'helpstr += "td, th {border: 1px solid #ddd;  padding: 6px;}"'
    outstr += nlind + 'helpstr += "th {padding-top: 6px;padding-bottom: 6px;text-align: left;background-color: #0C6AA6; color: white;}"'
    outstr += nlind + 'helpstr += "</style></head>"'
    outstr += nlind + 'helpstr += "<body>"'

    # Open the workbook
    wb = load_workbook(filename = fname_in, read_only=False)

    # iterate through the sheets
    for ws in wb.worksheets:

        print(ws.title, "  ", ws.max_row, "rows  ", ws.max_column, "columns")

        # hack to work around when openpyxl seems more rows than actual
        num_rows = ws.max_row
        for max_row, row in enumerate(ws, 1):
            if all(c.value is None for c in row):
                if max_row == num_rows + 2:
                    break
            else:
                num_rows = max_row
        
        # create the table name for the sheet name
        tbl_name = 'tbl_' + re.sub(r"[^A-Za-z0-9]",'',ws.title)

        # build a formatted list of all rows in the sheet
        all_rows = generateRows(ws)

        # build a title string from the first row of the sheet
        titlestr = getTitle(all_rows,ws, wb.index(ws))
        #print("titlestr", titlestr)

        # build a top notes table if there are any topnotes
        tbl_topnotes, nrows_topnotes = getNotes(all_rows,num_rows,tbl_name,notetype='top')
        #print("topnotes " + str(nrows_topnotes) + str("\n") + str(tbl_topnotes))

        # build a bottom notes table if there are any bottomnotes
        tbl_bottomnotes, nrows_bottomnotes = getNotes(all_rows,num_rows,tbl_name,notetype='bottom')
        #print("bottomnotes " + str(nrows_bottomnotes) + str("\n") + str(tbl_bottomnotes))
        
        # build the table components for the header row and the data rows
        if len(all_rows) > 1 + nrows_topnotes:
            tbl_fieldnames = getFieldnames(all_rows[1+nrows_topnotes],tbl_name)
            #print("tbl_fieldnames",tbl_fieldnames)
            tbl_addrows = getAddrows(all_rows[2+nrows_topnotes:num_rows-nrows_bottomnotes],tbl_name)
            #print("tbl_addrows\n" + tbl_addrows)
        else:
            tbl_fieldnames = ""
            tbl_addrows = ""
        
        # assemble the py code in outstr 
        # add the title
        outstr += titlestr
        
        # add  top notes
        if nrows_topnotes > 0:
            outstr += tbl_topnotes
            outstr += nlind + 'helpstr += ' + tbl_name + 'top' + '.get_html_string(attributes={' + note_table_attributes + '})'

        # add the data table with header
        if len(tbl_addrows) > 0:
            outstr += nlind + tbl_name + ' = prettytable.PrettyTable()'
            outstr += nlind + tbl_fieldnames
            outstr += nlind + tbl_addrows
            outstr += nlind + 'helpstr += ' + tbl_name + '.get_html_string(attributes={' + data_table_attributes + '})'

        # add bottom notes
        if nrows_bottomnotes > 0:
            outstr += tbl_bottomnotes
            outstr += nlind + 'helpstr += ' + tbl_name + 'bottom' + '.get_html_string(attributes={' + note_table_attributes + '})'
        
    # finalize outstr - py code
    outstr += nlind + 'helpstr += "</body>"'
    
    # add ugly stuff to clean the nbsp entity that gets escaped in the html output by PrettyTable
    outstr += nlind + 'helpstr = re.sub(r"&amp;#160;", r"&#160;",helpstr)'

    # add trailer
    outstr += '\n'
    outstr += nlind + '# autogenerated help pasted above'
    outstr += '\n'
    outstr += '\n# ----- Cut above ---------------------------------------------'
    # write to named html file
    outstr += '\n' + "outfile = open('" + fname_out_html + "','w')"
    outstr += '\n' + 'outfile.write(helpstr)'
    outstr += '\n' + 'outfile.close()'
    # write output to a generic filename
    outstr += '\n' + "outfile = open('../output_files/help.html','w')"
    outstr += '\n' + 'outfile.write(helpstr)'
    outstr += '\n' + 'outfile.close()'

    return outstr

if __name__ == "__main__":
    
#    if len(sys.argv) > 1:
#        fname_in =  join(dirname(abspath(__file__)), 'input_files',  sys.argv[1] + '.xlsx')
#        fname_out = join(dirname(abspath(__file__)), 'output_files', sys.argv[1] + '.py')
#        fname_out_html = join(dirname(abspath(__file__)), 'output_files', sys.argv[1] + '.html')
    if len(sys.argv) > 1:
        fname_in =  '../input_files/' + sys.argv[1] + '.xlsx'
        fname_out = '../output_files/' + sys.argv[1] + '.py'
        fname_out_html = '../output_files/' + sys.argv[1] + '.html'
    else:  #for testing
        fname_in = '../input_files/test.xlsx'
        fname_out = '../output_files/test.py'
        fname_out_html = '../output_files/test.html'

    outstr = buildpyCode(fname_in,fname_out_html)
#    print(outstr)
#    print(fname_out)

    # write outstr (py code) to the specified filename
    outfile = open(fname_out,'w')
    outfile.write(outstr)
    outfile.close()

    # create HTML files for inspection by executing the py code file
    subprocess.call(["python", fname_out])
