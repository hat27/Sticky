#-*- coding: utf8 -*-
import re

def split_shot(unique, value):
    find_all = re.findall("s(.*)c(.*)", value)
    if find_all:
        find_all = find_all[0]
        if unique == "scene":
            value = "s%s" % find_all[0]
        elif unique == "cut":
            value = "c%s" % find_all[1]

    return value

def execute(keys, field_value):
    for key in keys:
        if not "{" in key:
            continue

        name, unique = re.findall("(.*){(.*)}", key)[0]
        name = key.replace("{%s}" % unique, "")

        if not name in field_value:
            continue

        value = split_shot(unique, field_value[name])
        field_value[key] = value

    return field_value


