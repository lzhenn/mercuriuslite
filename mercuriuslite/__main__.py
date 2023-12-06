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
import datetime

from .lib import cfgparser, utils, const, io, messenger

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

package_name = 'mercuriuslite'

# path to the top-level handler
CWD=sys.path[0]

# path to this module
#MWD=os.path.split(os.path.realpath(__file__))[0]
   
class Mercurius:
    '''
    Mercurius is a class to drive the system
    '''

    def __init__(self, cfgfn='config.case.ini'):
        self._setup_logging()

        if not(os.path.exists(os.path.join(CWD,cfgfn))):
            utils.write_log('config file not exist, copy from pkg...')
            copy_cfg(os.path.join(CWD,cfgfn))
        
        self.cfg=cfgparser.read_cfg(os.path.join(CWD,cfgfn))
        self.ltm_dir=self.cfg['MERCURIUS']['ltm_dir']
        self.model_path=self.cfg['MERCURIUS']['model_path']

        const.init(self.cfg)
        
        utils.write_log('Mercurius Initiation Done.')
    def as_crawler(self):
        from .lib import crawler
        self.crawler=crawler.Andariel(self)
    
    def as_predictor(self):
        from .model import oculus
        self.predictor=oculus.Oculus(self)
    
    def as_inspector(self):
        from .eval import metatron
        self.inspector=metatron.Metatron(self)
        
    def as_evaluator(self, predictor):
        '''single model evaluator'''
        from .eval import iustitia
        self.evaluator=iustitia.Iustitia(predictor, self.cfg)
    
    def as_referee(self):
        '''single target strategy referee'''    
        from .eval import prudentia
        self.referee=prudentia.Prudentia(self)

    def as_trader(self):
        from .strategy import minerva
        self.trader=minerva.Minerva(self)
    
    def _setup_logging(self):
        """
        Configures the logging module using the 
        'config.logging.ini' file in the installed package.
        """
        resource_path = os.path.join('conf','config.logging.ini')
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
    resource_path = os.path.join('conf','config.case.ini')
    try:
        src_path = pkg_resources.resource_filename(
            package_name, resource_path)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Config file '{resource_path}' not found in '{package_name}'.")
    shutil.copy2(src_path, dest_path)

def resend_msg(cfg):
    msg_dic=io.load_msg(cfg['SCHEMER']['out_msg_file'])
    date=datetime.datetime.now().strftime('%Y-%m-%d')
    predate=msg_dic['date']
    title=msg_dic['title'].replace(predate,date)
    content=msg_dic['msg_body'].replace(predate,date)
    messenger.gmail_send_message(cfg, title, content)


