#!/usr/bin/env python
# _*_ coding:utf-8 _*_
import json
import os

import requests
import xmind
import logging
import time

from .parser import xmind_to_testsuites
from ApiManager.models import XmindCase, UserInfo
# from django.utils import timezone


def get_absolute_path(path):
    """
        Return the absolute path of a file

        If path contains a start point (eg Unix '/') then use the specified start point
        instead of the current working directory. The starting point of the file path is
        allowed to begin with a tilde "~", which will be replaced with the user's home directory.
    """
    fp, fn = os.path.split(path)
    if not fp:
        fp = os.getcwd()
    fp = os.path.abspath(os.path.expanduser(fp))
    return os.path.join(fp, fn)


def get_xmind_testsuites(xmind_file):
    """Load the XMind file and parse to `xmind2testcase.metadata.TestSuite` list"""
    xmind_file = get_absolute_path(xmind_file)
    workbook = xmind.load(xmind_file)
    xmind_content_dict = workbook.getData()
    logging.debug("loading XMind file(%s) dict data: %s", xmind_file, xmind_content_dict)

    if xmind_content_dict:
        testsuites = xmind_to_testsuites(xmind_content_dict)
        return testsuites
    else:
        logging.error('Invalid XMind file(%s): it is empty!', xmind_file)
        return []


def get_xmind_testsuite_list(xmind_file):
    """Load the XMind file and get all testsuite in it

    :param xmind_file: the target XMind file
    :return: a list of testsuite data
    """
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to testsuite data list...', xmind_file)
    testsuite_list = get_xmind_testsuites(xmind_file)
    suite_data_list = []

    for testsuite in testsuite_list:
        product_statistics = {'case_num': 0, 'non_execution': 0, 'pass': 0, 'failed': 0, 'blocked': 0, 'skipped': 0}
        for sub_suite in testsuite.sub_suites:
            suite_statistics = {'case_num': len(sub_suite.testcase_list), 'non_execution': 0,
                                'pass': 0, 'failed': 0, 'blocked': 0, 'skipped': 0}
            for case in sub_suite.testcase_list:
                if case.result == 0:
                    suite_statistics['non_execution'] += 1
                elif case.result == 1:
                    suite_statistics['pass'] += 1
                elif case.result == 2:
                    suite_statistics['failed'] += 1
                elif case.result == 3:
                    suite_statistics['blocked'] += 1
                elif case.result == 4:
                    suite_statistics['skipped'] += 1
                else:
                    logging.warning('This testcase result is abnormal: %s, please check it: %s',
                                    case.result, case.to_dict())
            sub_suite.statistics = suite_statistics
            for item in product_statistics:
                product_statistics[item] += suite_statistics[item]

        testsuite.statistics = product_statistics
        suite_data = testsuite.to_dict()
        suite_data_list.append(suite_data)

    logging.info('Convert XMind file(%s) to testsuite data list successfully!', xmind_file)
    return suite_data_list


def get_xmind_testcase_list(xmind_file):
    """Load the XMind file and get all testcase in it

    :param xmind_file: the target XMind file
    :return: a list of testcase data
    """
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to testcases dict data...', xmind_file)
    testsuites = get_xmind_testsuites(xmind_file)
    testcases = []

    for testsuite in testsuites:
        product = testsuite.name
        for suite in testsuite.sub_suites:
            for case in suite.testcase_list:
                case_data = case.to_dict()
                case_data['product'] = product
                case_data['suite'] = suite.name
                testcases.append(case_data)

    logging.info('Convert XMind file(%s) to testcases dict data successfully!', xmind_file)
    return testcases


def xmind_testsuite_to_json_file(xmind_file):
    """Convert XMind file to a testsuite json file"""
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to testsuites json file...', xmind_file)
    testsuites = get_xmind_testsuite_list(xmind_file)
    testsuite_json_file = xmind_file[:-6] + '_testsuite.json'

    if os.path.exists(testsuite_json_file):
        logging.info('The testsuite json file already exists, return it directly: %s', testsuite_json_file)
        return testsuite_json_file

    with open(testsuite_json_file, 'w', encoding='utf8') as f:
        f.write(json.dumps(testsuites, indent=4, separators=(',', ': ')))
        logging.info('Convert XMind file(%s) to a testsuite json file(%s) successfully!',
                     xmind_file, testsuite_json_file)

    return testsuite_json_file


def xmind_testcase_to_json_file(xmind_file):
    """Convert XMind file to a testcase json file"""
    xmind_file = get_absolute_path(xmind_file)
    logging.info('Start converting XMind file(%s) to testcases json file...', xmind_file)
    testcases = get_xmind_testcase_list(xmind_file)
    testcase_json_file = xmind_file[:-6] + '.json'

    if os.path.exists(testcase_json_file):
        logging.info('The testcase json file already exists, return it directly: %s', testcase_json_file)
        return testcase_json_file

    with open(testcase_json_file, 'w', encoding='utf8') as f:
        f.write(json.dumps(testcases, indent=4, separators=(',', ': ')))
        logging.info('Convert XMind file(%s) to a testcase json file(%s) successfully!', xmind_file, testcase_json_file)

    return testcase_json_file


def handle_upload(file, folder, user):

    current = time.strftime("%Y-%m-%d", time.localtime())
    timestamp = str(int(time.time()))
    format_name = user + '-' + current + '(' + timestamp + ')' + '-'
    with open(folder + '\\' + format_name + file.name, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    return format_name + file.name


def case_to_db(testcases, user, xmind_file, xlsx_file, filename):
    """
    :param testcases:
    :param user:
    :param xmind_file:
    :param xlsx_file:
    :param filename
    :return:
    table structure:
    项目 模块 子模块 标题 步骤/预期 作者 文件路径 属性=优先级&用例类型
    """
    user_id = UserInfo.objects.get(username=user).id
    for case in testcases:
        xmindcase = XmindCase()
        xmindcase.belong_project = case['product']
        xmindcase.suite = case['suite']
        xmindcase.belong_module = case['module']
        xmindcase.steps = case['steps']
        xmindcase.name = case['name']
        xmindcase.author = user_id
        xmindcase.attributes = {"importance": case['importance'], "execution_type": case['execution_type']}
        xmindcase.xmind_file.name = xmind_file
        xmindcase.xlsx_file.name = xlsx_file
        xmindcase.file_name = filename
        xmindcase.save()


def get_recent_records():
    records = []
    files = XmindCase.objects.values('xmind_file').distinct()
    for file in files:
        timequery = XmindCase.objects.filter(xmind_file=file['xmind_file']).values('create_time')[:1]
        filetime = list(timequery)[0]['create_time'].strftime("%Y-%m-%d %H:%M:%S")
        filequery = XmindCase.objects.filter(xmind_file=file['xmind_file']).values('xlsx_file', 'xmind_file').distinct()
        xmindfile = filequery[0]['xmind_file'].split('\\')[-1]
        xlsx = filequery[0]['xlsx_file'].split('\\')[-1]
        records.append({"name": xmindfile, "time": filetime, "xmind_file": xmindfile, "xlsx_file": xlsx})
    records.reverse()
    return records


def get_case_from_db(file):
    test_cases = []
    query = XmindCase.objects.filter(xmind_file=file).values('suite', 'belong_project', 'steps', 'belong_module',
                                                             'name', 'attributes')
    for case in query:
        suite = case['suite']
        product = case['belong_project']
        dbstep = case['steps']
        print('************' + case['name'])
        try:
            steps = json.loads(dbstep.replace(r'"', r'\"').replace('\'', '"'))
            module = case['belong_module']
            name = case['name']
            attr = case['attributes'].replace('\'', '"')
            attributes = json.loads(attr)
            importance = attributes['importance']
            execution_type = attributes['execution_type']
            casedict = {"module": module, "name": name, "execution_type": execution_type, "importance": importance,
                        "steps": steps, "product": product, "suite": suite}
            test_cases.append(casedict)
        except Exception as e:
            print(e)

    return test_cases


def get_metadata(env, message_class):
    """
    :param env: env is a dict include url and ssl token
    :param message_class
    :return: is a list like this: [{'channel': 'channel1', 'key': 'aaaaa', 'uuid': 'bbbbb',
    'deviceTypes': ['' , '', '']},{}]
    """
    env = {"url": "https://10.101.12.4:17998", "token": "063f2acb8048a8af15074f0387aeda1b"}
    url = env['url'] + '/ciimc-fe-api/meta/subscribe-change'
    filter = None
    params = {"token": env['token'], "message_class": message_class}
    with requests.get(url=url, params=params, stream=True, verify=False) as response:
        meta = []
        for chunk in response.iter_lines(chunk_size=1):
            chunk = chunk.decode('utf-8')
            if chunk:
                if chunk == 'change':
                    break
                else:
                    data = json.loads(chunk)
                    if message_class == 'channel':
                        meta.append(data['record']['name'])
                    elif message_class == 'api-key':
                        channel = data['record']['channel']
                        key = data['record']['key']
                        uuid = data['record']['uuid']
                        devicetypes = data['record']['deviceTypes']
                        meta.append({"channel": channel, "key": key, "uuid": uuid, "deviceTypes": devicetypes})
    return meta


def get_token(env, channel):
    env = {"url": "http://10.101.12.4:10099"}
    url = env['url'] + '/v2/auth'
    channels = get_metadata(env=[], message_class='api-key')
    for chan in channels:
        if channel == chan['channel']:
            key = chan['key']
            break
    params = {"key": key}
    with requests.get(url=url, params=params) as response:
        token = response.json()['token']
    return token
