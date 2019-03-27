#!/usr/bin/python3

import argparse
import json
import os
import errno

VERSION = 'v0.1.0'


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def safe_open_w(path):
    mkdir_p(os.path.dirname(path))
    return open(path, 'w')


def write_file_lines(path, data):
    with safe_open_w(path) as file:
        file.writelines(data)


def read_file_json(path):
    with open(path) as file:
        return json.load(file)


def has_diff(data):
    if len(data['differences']) != 0 or len(data['not found']) != 0 or len(data['not declared']) != 0:
        return True
        
    return False


def decode_ports(ports, messages, tab):
    for loc_port, vals in ports.items():
        rem_ip = vals['ip']
        rem_name = vals['name']
        rem_port = vals['port']
        m = tab + 'port {} is connected to port {} of the switch with the address "{}" and name "{}"'.format(
            loc_port, rem_port, rem_ip, rem_name)
        messages.append(m + '\n')


def decode_not_declared(not_declared, messages):
    for host, vals in not_declared.items():
        ip = vals['ip']
        name = vals['name']
        ports = vals['ports']
        m = 'Undocumented switch with address "{}", name "{}", and following ports detected:'.format(ip, name)
        messages.append(m + '\n')

        decode_ports(ports, messages, '\t')

    
def decode_not_found(not_found, messages):
    for host, vals in not_found.items():
        ip = vals['ip']
        name = vals['name']
        ports = vals['ports']
        m = 'Switch with address "{}", name "{}", and following ports not found:'.format(ip, name)
        messages.append(m + '\n')

        decode_ports(ports, messages, '\t')


def decode_not_declared_field(not_declared, messages, tab):
    for key, val in not_declared.items():
        if key == 'ports':
            m = tab + 'following ports not declared:'
            messages.append(m + '\n')
            decode_ports(val, messages, '\t\t')


def decode_not_found_field(not_found, messages, tab):
    for key, val in not_found.items():
        if key == 'ports':
            m = tab + 'following ports not found:'
            messages.append(m + '\n')
            decode_ports(val, messages, '\t\t')
                

def decode_differences(defferences, messages):
    for key, val in defferences.items():
        if key == 'ports':
            m = '\tfollowing ports have differences with the declared data:'
            messages.append(m + '\n')
            for loc_port, v in val.items():
                m = '\t\tport {}'.format(loc_port)
                messages.append(m + '\n')
                
                for field, f in v.items():
                    if field == 'ip':
                        m = '\t\t\tconnected to switch with the address "{}" instead of address "{}"'.format(
                        f['real'], f['declared'])
                        messages.append(m + '\n')
                    if field == 'name':
                        m = '\t\t\tconnected to the switch with name {} instead of name "{}"'.format(
                        f['real'], f['declared'])
                        messages.append(m + '\n')
                    if field == 'port':
                        m = '\t\t\tconnected to port {} instead of port {}'.format(
                        f['real'], f['declared'])
                        messages.append(m + '\n')
    
def decode_found(found, messages):
    for host, vals in found.items():
        if has_diff(vals):
            name = vals['matches']['name']
            m = 'Switch with address "{}" and name "{}" has differences with the declared data:'.format(host, name)
            messages.append(m + '\n')

            decode_not_declared_field(vals['not declared'], messages, '\t')
            
            decode_not_found_field(vals['not found'], messages, '\t')

            decode_differences(vals['differences'], messages)
            
            messages.append('\n')


def decode(input_path, output_path):
    input = read_file_json(input_path)
    messages = []

    decode_not_declared(input['not declared'], messages)

    decode_not_found(input['not found'], messages)

    decode_found(input['found'], messages)
            
    write_file_lines(output_path, messages)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s {}'.format(VERSION))
    parser.add_argument('input_file', help='input file path (json)')
    parser.add_argument('output_file', help='output file path (plain text)')

    args = parser.parse_args()

    decode(args.input_file, args.output_file)
