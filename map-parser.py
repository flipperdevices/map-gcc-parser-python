import os
import re
import sys
from typing import TextIO

from cxxfilt import demangle


class Objectfile:
    def __init__(self, section, offset, size, comment):
        self.section = section.strip()
        self.offset = offset
        self.size = size
        self.path = (None, None)
        self.basepath = None
        if comment:
            self.path = re.match(r'^(.+?)(?:\(([^\)]+)\))?$', comment).groups()
            self.basepath = os.path.basename(self.path[0])
        self.children = []

    def __repr__(self):
        return '<Objectfile {} {:x} {:x} {} {}>'.format(self.section, self.offset, self.size, self.path,
                                                        repr(self.children))


def parseSections(fd):
    """
    Quick&Dirty parsing for GNU ld’s linker map output, needs LANG=C, because
    some messages are localized.
    """

    sections = []
    with open(fd, 'r') as file:
        # skip until memory map is found
        found = False
        while True:
            l = file.readline()
            if not l:
                break
            if l.strip() == 'Memory Configuration':
                found = True
                break
        if not found:
            return None

        # long section names result in a linebreak afterwards
        sectionre = re.compile(
            '(?P<section>.+?|.{14,}\n)[ ]+0x(?P<offset>[0-9a-f]+)[ ]+0x(?P<size>[0-9a-f]+)(?:[ ]+(?P<comment>.+))?\n+',
            re.I)
        subsectionre = re.compile('[ ]{16}0x(?P<offset>[0-9a-f]+)[ ]+(?P<function>.+)\n+', re.I)
        s = file.read()
        pos = 0
        while True:
            m = sectionre.match(s, pos)
            if not m:
                # skip that line
                try:
                    nextpos = s.index('\n', pos) + 1
                    pos = nextpos
                    continue
                except ValueError:
                    break
            pos = m.end()
            section = m.group('section')
            v = m.group('offset')
            offset = int(v, 16) if v is not None else None
            v = m.group('size')
            size = int(v, 16) if v is not None else None
            comment = m.group('comment')
            if section != '*default*' and size > 0:
                of = Objectfile(section, offset, size, comment)
                if section.startswith(' '):
                    index = -1
                    last_same_address_item_index = -1
                    children = []
                    sections[-1].children.append(of)
                    while True:
                        m = subsectionre.match(s, pos)
                        if not m:
                            break
                        pos = m.end()
                        offset, function = m.groups()
                        offset = int(offset, 16)
                        if sections and sections[-1].children:
                            index += 1
                            if offset == of.offset:
                                last_same_address_item_index = index
                            children.append([offset, 0, function])
                    if children:
                        children[last_same_address_item_index][1] = of.size
                    sections[-1].children[-1].children.extend(children)
                else:
                    sections.append(of)

        return sections


def get_subsection_name(section_name: str, subsection: Objectfile) -> str:
    if subsection.section.startswith('.'):
        subsection_split_names = subsection.section[1:].split('.')
    else:
        subsection_split_names = subsection.section.split('.')

    return f'.{subsection_split_names[1]}' if len(subsection_split_names) > 2 else section_name


def write_subsection(
    section_name: str,
    subsection_name: str,
    address: str,
    size: int,
    demangled_name: str,
    module_name: str,
    file_name: str,
    mangled_name: str,
    write_file_object: TextIO
) -> None:
    write_file_object.write(
        f'{section_name}\t'
        f'{subsection_name}\t'
        f'{address}\t'
        f'{size}\t'
        f'{demangled_name}\t'
        f'{module_name}\t'
        f'{file_name}\t'
        f'{mangled_name}\n'
    )


def save_subsection(section_name: str, subsection: Objectfile, write_file_object: TextIO) -> None:
    subsection_name = get_subsection_name(section_name, subsection)
    module_name = subsection.path[0]
    file_name = subsection.path[1]

    if not file_name:
        file_name, module_name = module_name, ''

    if not subsection.children:
        address = f'{subsection.offset:x}'
        size = subsection.size
        mangled_name = '' if subsection.section == section_name else subsection.section.split(".")[-1]
        demangled_name = demangle(mangled_name) if mangled_name else mangled_name

        write_subsection(
            section_name=section_name, subsection_name=subsection_name,
            address=address, size=size,
            demangled_name=demangled_name, module_name=module_name,
            file_name=file_name, mangled_name=mangled_name,
            write_file_object=write_file_object
        )
        return

    for subsection_child in subsection.children:
        address = f'{subsection_child[0]:x}'
        size = subsection_child[1]
        mangled_name = subsection_child[2]
        demangled_name = demangle(mangled_name)

        write_subsection(
            section_name=section_name,
            subsection_name=subsection_name,
            address=address,
            size=size,
            demangled_name=demangled_name,
            module_name=module_name,
            file_name=file_name,
            mangled_name=mangled_name,
            write_file_object=write_file_object
        )


def save_section(section: Objectfile, write_file_object: TextIO) -> None:
    section_name = section.section
    for subsection in section.children:
        save_subsection(section_name=section_name, subsection=subsection, write_file_object=write_file_object)


def save_parse_data(parse_data: list[Objectfile], output_file_name: str) -> None:
    with open(output_file_name, 'w') as write_file_object:
        for section in parse_data:
            if section.children:
                save_section(section=section, write_file_object=write_file_object)


if __name__ == '__main__':
    save_parse_data(parseSections(sys.argv[1]), sys.argv[2])
