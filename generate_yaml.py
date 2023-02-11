#!/usr/bin/python3

import sys
import os
import glob
import argparse
import yaml
import jinja2

def generate_single_files(context_filename, template_filename, output_filename):

    ########### loading
    with open(context_filename) as file :
        try:
            context_dict=yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(exc)

    ########### custom jinja globals
    def exception(msg):
        raise Exception(msg)

    def format_list(list_, pattern):
        return [pattern % s for s in list_]


    ########### draft / intial validation
    #validate context and extend config
    if "spec" not in context_dict:
        exception("Error: No key .spec existing !")

    if not context_dict["spec"]["containers"]:
        exception("Error: No container existing in .spec.containers !")

    # create states.EXECUTE, if not exist
    if "states" not in context_dict["spec"]:
        context_dict["spec"]["states"]=[]

    #TODO: add rule for adding states automatically
    if "INSTALL" not in context_dict["spec"]["states"]:
        context_dict["spec"]["states"]+=["INSTALL"]

    if "EXECUTE" not in context_dict["spec"]["states"]:
        context_dict["spec"]["states"]+=["EXECUTE"]

    if "shared_volume" not in context_dict["spec"]:
        exception("Error: No shared volume .spec.shared_volume not defined !")

    #check references for existing definitions
    for container in context_dict["spec"]["containers"]:

        #mandatory
        if "image" not in context_dict["spec"]["containers"][container]:
            exception("Error: Image .spec.%s.image not defined !" % container)

        #optional
        if "sync" in context_dict["spec"]["containers"][container]:
            for state in context_dict["spec"]["containers"][container]["sync"]:

                if state not in context_dict["spec"]["states"]:
                    exception("Error: State reference .spec.%s.sync.%s not defined in .spec.states=%s !" % (container, state, context_dict["spec"]["states"]) )

                for c in context_dict["spec"]["containers"][container]["sync"][state]:
                    if c not in context_dict["spec"]["containers"]:
                        exception("Error: Container reference .spec.%s.sync.%s.%s not defined in .spec.containers=%s !" % (container, state, c, list(context_dict["spec"]["containers"].keys())) )

    #TODO: SCHEMA + VALIDATION NEEDED
    #TODO: check commands existing
    #TODO: ensure for all commands to have .strip("\n ;")
    #TODO: check for cycles

    ########### draft / intial extension
    WAITS={}
    WAIT_FOR={}

    for container in context_dict["spec"]["containers"]:
        WAIT_FOR[container]={}
        WAITS[container]={}

        for state in context_dict["spec"]["states"]:
            WAIT_FOR[container][state]=[]
            WAITS[container][state]=False

    for cK,cV in context_dict["spec"]["containers"].items():
        for state in context_dict["spec"]["states"]:

            if "sync" not in cV or state not in cV["sync"]:
                continue

            for c in cV["sync"][state]:

                WAIT_FOR[cK][state]+=[c]
                WAITS[c][state]|=True

    context_dict["internal"]={"WAITS": WAITS, "WAIT_FOR": WAIT_FOR}


    ########### template engine
    environment = jinja2.Environment()

    ########### add globals
    environment.globals['format_list'] = format_list
    environment.globals['exception'] = exception # use from template via: {{ exception("uh oh...") }}

    ########### read (and load) one template from file (no FileSystemLoader for now)
    with open(template_filename, 'r') as template_f:
        template = environment.from_string(template_f.read())

    ########### render
    compose_output=template.render(context_dict)

    #TODO: validate/flatten/format before writing file

    ########### write one file
    with open(output_filename, 'w') as f:
        f.write(compose_output)


    ########### write one file
    with open(output_filename, 'w') as f:
        f.write(compose_output)

    ########### overwrite with fattened file
    # yaml.Dumper.ignore_aliases = lambda *args: True

    # def str_presenter(dumper, data):
    #     if data.count('\n') > 0:  # check for multiline string
    #         return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    #     return dumper.represent_scalar('tag:yaml.org,2002:str', data)
    # yaml.add_representer(str, str_presenter)

    # data_no_alias = yaml.safe_load(compose_output)

    # with open(output_filename, 'w') as f:
    #     f.write(yaml.dump(data_no_alias, allow_unicode=True))


def main():

    """@brief main function"""
    parser = argparse.ArgumentParser(description='Generate YAML specification based on Multi-Container-Job Templates.')

    parser.add_argument('-c', '--context', default="./contexts/context.yaml")
    parser.add_argument('-t', '--template', default="./templates/compose.j2.yaml")
    parser.add_argument('-o', '--output', default="./output/compose.yaml")


    args = parser.parse_args()

    if args.context and  args.template and args.output :
        generate_single_files(args.context, args.template, args.output)
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())