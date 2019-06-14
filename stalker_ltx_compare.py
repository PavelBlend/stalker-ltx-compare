import tkinter
from tkinter import filedialog


class StalkerLtxParser:
    WHITESPACE = {' ', '\t'}
    COMMENT = {';', '/'}

    class LtxSection:
        def __init__(self, name, parent):
            self.name = name
            self.parent = parent
            self.params = {}

    def __init__(self, path):
        file = open(path, 'r')
        self.data = file.read()
        file.close()
        self.parse()

    def parse(self):
        parse_lines = []
        for line in self.data.split('\n'):
            parse_line = ''
            for char in line:
                if char in self.WHITESPACE:
                    continue
                if char in self.COMMENT:
                    break
                parse_line += char
            if parse_line:
                parse_lines.append(parse_line)
        line_index = 0
        lines_count = len(parse_lines)
        self.sections = {}
        while line_index < lines_count:
            line = parse_lines[line_index]
            if line[0] == '[':
                split_char = ']'
                if ':' in line:
                    split_char += ':'
                    section_name, section_parent = line.split(split_char)
                    section_name = section_name[1 : ]    # cut "["
                else:
                    section_name = line.split(split_char)[0][1 : ]
                    section_parent = None
                section = self.LtxSection(section_name, section_parent)
                self.sections[section_name] = section
                start_new_section = False
                line_index += 1
                while not start_new_section and line_index < lines_count:
                    line = parse_lines[line_index]
                    if line[0] == '[':
                        start_new_section = True
                    else:
                        if '=' in line:
                            param_name, param_value = line.split('=')
                        else:
                            param_name = line
                            param_value = None
                        section.params[param_name] = param_value
                        line_index += 1
            elif line.startswith('#include'):
                line_index += 1


class CompareParams:
    def __init__(self):
        self.deleted_params = {}
        self.added_params = {}
        self.edit_params = {}


class CompareSections:
    def __init__(self):
        self.deleted_sections = []
        self.added_sections = {}
        self.edit_sections = {}
        self.compare_params = {}


def run_compare_ltx(orig, edit, out):
    orig_ltx = StalkerLtxParser(orig)
    edit_ltx = StalkerLtxParser(edit)
    compare_ltx = CompareSections()

    for section_name, section in orig_ltx.sections.items():
        edit_section = edit_ltx.sections.get(section_name, None)
        if not edit_section:
            compare_ltx.deleted_sections.append(section_name)
            continue
        compare_params = CompareParams()
        compare_ltx.compare_params[section_name] = compare_params
        for param_name, param_value in section.params.items():
            edit_param_value = edit_section.params.get(param_name, None)
            if edit_param_value is None:
                compare_ltx.compare_params[section_name].deleted_params[param_name] = param_value
                if not compare_ltx.edit_sections.get(section_name, None):
                    compare_ltx.edit_sections[section_name] = section
                continue
            if param_value != edit_param_value:
                compare_ltx.compare_params[section_name].edit_params[param_name] = [param_value, edit_param_value]
                if not compare_ltx.edit_sections.get(section_name, None):
                    compare_ltx.edit_sections[section_name] = section

    for section_name, section in edit_ltx.sections.items():
        if not orig_ltx.sections.get(section_name, None):
            compare_ltx.added_sections[section_name] = section
        else:
            for param_name, param_value in section.params.items():
                orig_section = orig_ltx.sections[section_name]
                if orig_section.params.get(param_name, None) is None:
                    compare_ltx.compare_params[section_name].added_params[param_name] = param_value
                    if not compare_ltx.edit_sections.get(section_name, None):
                        compare_ltx.edit_sections[section_name] = section

    output = '; Результат сравнения файлов:\n'
    output += '; {}\n'.format(orig)
    output += '; {}\n'.format(edit)
    if compare_ltx.deleted_sections:
        output += '\n\n; Удалённые секции:\n\n'
        for deleted_section_name in compare_ltx.deleted_sections:
            output += '[{}]\n'.format(deleted_section_name)

    if compare_ltx.added_sections:
        output += '\n\n; Добавленные секции и их параметры:\n\n'
        for added_section_name, added_section in compare_ltx.added_sections.items():
            output += '[{}]\n'.format(added_section_name)
            for param_name, param_value in added_section.params.items():
                output += '    ' + param_name + '\n'

    if compare_ltx.edit_sections:
        output += '\n\n; Изменённые секции и их параметры:\n\n'
        for edit_section_name, edit_section in compare_ltx.edit_sections.items():
            output += '[{}]\n'.format(edit_section_name)
            if compare_ltx.compare_params[edit_section_name].edit_params:
                output += '\n; Изменено:\n\n'
                for param_name, (old_value, new_value) in compare_ltx.compare_params[edit_section_name].edit_params.items():
                    output += '    {0}: {1} > {2}\n'.format(param_name, old_value, new_value)
            if compare_ltx.compare_params[edit_section_name].deleted_params:
                output += '\n\n; Удалено:\n\n'
                for param_name, param_value in compare_ltx.compare_params[edit_section_name].deleted_params.items():
                    output += '    {0}: {1}\n'.format(param_name, param_value)
            if compare_ltx.compare_params[edit_section_name].added_params:
                output += '\n\n; Добавлено:\n\n'
                for param_name, param_value in compare_ltx.compare_params[edit_section_name].added_params.items():
                    output += '    {0}: {1}\n'.format(param_name, param_value)

    output_file = open(out, 'w')
    output_file.write(output)
    output_file.close()


class UserInterface:
    def __init__(self):
        self.root = tkinter.Tk()
        self._modify_root_window()
        self._add_entrys()
        self._add_buttons()

    def _modify_root_window(self):
        self.root.title('STALKER *.ltx Compare')
        self.root.resizable(height=False, width=False)
        width = 600
        height = 150
        header_size = 50
        self.root.minsize(width=width, height=height)
        self.root.maxsize(width=width, height=height)
        pos_x = (self.root.winfo_screenwidth()) / 2
        pos_y = (self.root.winfo_screenheight()) / 2 - header_size
        self.root.geometry('+{0}+{1}'.format(
            int(pos_x - width / 2), int(pos_y - height / 2)
        ))

    def compare_ltx(self):
        orig_file_path = self.entry_original.get()
        if not orig_file_path:
            return
        edit_file_path = self.entry_edit.get()
        if not edit_file_path:
            return
        out_file_path = self.entry_out.get()
        if not out_file_path:
            return
        run_compare_ltx(orig_file_path, edit_file_path, out_file_path)

    def open_orig(self):
        file_name = filedialog.askopenfilename(
            defaultextension='.ltx',
            filetypes=[('STALKER Config', '.ltx'), ('all files', '.*')],
            title='Выберите оригинальный ltx файл'
        )
        self.entry_original.delete(0, tkinter.END)
        self.entry_original.insert(0, file_name)

    def open_edit(self):
        file_name = filedialog.askopenfilename(
            defaultextension='.ltx',
            filetypes=[('STALKER Config', '.ltx'), ('all files', '.*')],
            title='Выберите изменённый ltx файл'
        )
        self.entry_edit.delete(0, tkinter.END)
        self.entry_edit.insert(0, file_name)

    def open_out(self):
        file_name = filedialog.asksaveasfilename(
            defaultextension='.ltx',
            filetypes=[('STALKER Config', '.ltx'), ('all files', '.*')],
            title='Сохранить результат сравнения'
        )
        self.entry_out.delete(0, tkinter.END)
        self.entry_out.insert(0, file_name)

    def _add_buttons(self):
        button_original = tkinter.Button(
            self.root,
            text='Оригинальный *.ltx',
            width=20,
            command=self.open_orig
        )
        button_edit = tkinter.Button(
            self.root,
            text='Изменённый *.ltx',
            width=20,
            command=self.open_edit
        )
        button_out = tkinter.Button(
            self.root,
            text='Результат сравнения',
            width=20,
            command=self.open_out
        )
        button_compare = tkinter.Button(
            self.root,
            text='Сравнить',
            width=20,
            command=self.compare_ltx
        )
        button_original.grid(row=0, column=0, padx=0)
        button_edit.grid(row=1, column=0, padx=0)
        button_out.grid(row=2, column=0, padx=0)
        button_compare.grid(row=3, column=0, padx=0)

    def _add_entrys(self):
        self.entry_original = tkinter.Entry(self.root, width=85, font='Font 7')
        self.entry_edit = tkinter.Entry(self.root, width=85, font='Font 7')
        self.entry_out = tkinter.Entry(self.root, width=85, font='Font 7')
        self.entry_original.grid(row=0, column=1, padx=0, pady=5)
        self.entry_edit.grid(row=1, column=1, padx=5)
        self.entry_out.grid(row=2, column=1, padx=5)

    def mainloop(self):
        self.root.mainloop()


ui = UserInterface()
ui.mainloop()
