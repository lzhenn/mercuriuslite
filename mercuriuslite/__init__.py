#!/usr/bin/env python3
'''
Date: Jul 30, 2023
mercuriuslite is 

This is the main script to drive the model

History:
Jul 30, 2023 --- Kick off the project 

L_Zealot
'''
import sys, os
import logging, logging.config
import shutil
import pkg_resources

from .lib import cfgparser, utils


package_name = 'mercuriuslite'

# path to the top-level handler
CWD=sys.path[0]

# path to this module
#MWD=os.path.split(os.path.realpath(__file__))[0]


def _setup_logging():
    """
    Configures the logging module using the 
    'config.logging.ini' file in the installed package.
    """
    resource_path = 'conf/config.logging.ini'
    try:
        config_file = pkg_resources.resource_filename(
            package_name, resource_path)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Config file '{resource_path}' not found in '{package_name}'.")
    
    logging.config.fileConfig(
        config_file, disable_existing_loggers=False)


def copy_cfg(dest_path):
    """
    Copies a configuration file from the installed package to the destination path.

    Args:
        dest_path (str): The path of the destination configuration file.

    Raises:
        FileNotFoundError: If the configuration file does not exist in the package.
    """
    resource_path = 'conf/config.case.ini'
    try:
        src_path = pkg_resources.resource_filename(
            package_name, resource_path)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Config file '{resource_path}' not found in '{package_name}'.")
    shutil.copy2(src_path, dest_path)

def waterfall():
    '''
    Waterfall rundown!
    '''
    
    _setup_logging()


    if not(os.path.exists(CWD+'/config.case.ini')):
        utils.write_log('config file not exist, copy from pkg...')
        copy_cfg(os.path.join(CWD,'config.case.ini'))
    
    cfg=cfgparser.read_cfg(os.path.join(CWD,'config.case.ini'))
    
    
    utils.write_log('Main pipeline...')
    # driver.drive(cfg)