# coding=utf-8
"""

"""
import base64
import copy
import json
import logging
import os
import time
import uuid
from collections import deque

import jsonpickle
import jsonpickle.ext.numpy as jsonpickle_numpy

import audio_processing
import recommendations
import config
import nussl
import actions
import utils

# Set up logging
logger = logging.getLogger()

jsonpickle_numpy.register_handlers()


class SeparationSession(object):
    """
    Object for a single session, handles everything
    """
    _file_ext_that_need_converting = ['mp3', 'flac']

    def __init__(self, from_json=False):
        """

        """

        self.session_id = None
        self.base_audio_path = None
        self.user_original_file_folder = None
        self.time_of_birth = time.asctime(time.localtime(time.time()))
        self.time_of_init = None
        self._action_queue = deque()
        self.user_goals = []

        if not from_json:
            # Set up a session ID and store it
            self.session_id = uuid.uuid4()

            # Set up folders
            self.base_audio_path = config.USER_AUDIO_FOLDER
            self.user_original_file_folder = os.path.join(self.base_audio_path, self.url_safe_id,
                                                          config.USER_AUDIO_ORIGINAL_FOLDER_NAME)
            utils.safe_makedirs(self.user_original_file_folder)

            logger.info('New session ready! - {}'.format(self.url_safe_id))

        self.user_original_file_location = None
        self.user_general_audio = None
        self.ft2d = None
        self.duet = None

        self.sdr_predictor = None

        self.undo_list = []
        self.initialized = False

    @property
    def url_safe_id(self):
        # 22 chars long (last two chars are '==')
        return base64.urlsafe_b64encode(self.session_id.bytes)[:22]

    @property
    def stft_done(self):
        if self.user_general_audio is None:
            return False

        return self.user_general_audio.stft_done

    @property
    def target_name_dict(self):
        """
        This dictionary links the front end names to the back end objects
        """
        return {'mixture':  {'name': 'MixtureSpectrogram',  'object': self.user_general_audio},
                'duet':     {'name': 'AtnDelayHistogram',   'object': self.duet},
                'ft2d':     {'name': 'FT2D',                'object': self.ft2d},
                'result':   {'name': 'ResultSpectrogram',   'object': None} }

    @property
    def _target_dict_name_to_object(self):
        return {v['name']: v['object'] for v in self.target_name_dict.values()}

    def initialize(self, path_to_file):
        if not os.path.isfile(path_to_file):
            raise Exception('File path not a file! - {}'.format(path_to_file))

        self.user_original_file_location = path_to_file

        user_signal = nussl.AudioSignal(self.user_original_file_location)
        self.user_general_audio = audio_processing.GeneralAudio(user_signal, self.user_original_file_folder)
        self.ft2d = audio_processing.FT2D(user_signal, self.user_original_file_folder)

        if user_signal.is_stereo:
            self.duet = audio_processing.Duet(user_signal, self.user_original_file_folder)

        self.sdr_predictor = recommendations.SDRPredictor(self.user_general_audio.audio_signal_copy,
                                                          self.base_audio_path, self.user_goals, {})

        self.initialized = True
        self.time_of_init = time.asctime(time.localtime(time.time()))

    def receive_survey_response(self, survey_data):
        self.user_goals = survey_data['extraction_goals']
        self.sdr_predictor = recommendations.SDRPredictor(self.user_general_audio.audio_signal_copy,
                                                        self.base_audio_path, self.user_goals, {})

    @property
    def algorithms_run_yet(self):
        return self.sdr_predictor.algorithms_run_yet

    def push_action(self, action_dict):
        action_id = len(self._action_queue) + 1
        action = actions.Action.new_action(action_dict, action_id)

        action_entry = {'received': time.asctime(),
                        'owner': self.url_safe_id,
                        'action_id': action_id,
                        'action': action}

        self._action_queue.append(action_entry)

    def apply_actions_in_queue(self):

        while self._action_queue:
            action = self._action_queue.popleft()
            action_object = action['action']
            logger.debug('Applying {} - ID{}, got at {}'.format(str(action_object),
                                                                action['action_id'],
                                                                action['received']))

            if action_object.target not in self._target_dict_name_to_object.keys():
                raise actions.ActionException('Unknown target: {}!'.format(action_object.target))

            target = self._target_dict_name_to_object[action_object.target]
            action_object.make_mask_for_action(target)
            self.user_general_audio.audio_signal_copy = action_object.apply_action(target)

    def to_json(self):
        return jsonpickle.encode(self)

    @staticmethod
    def from_json(json_string):
        return jsonpickle.decode(json_string)
