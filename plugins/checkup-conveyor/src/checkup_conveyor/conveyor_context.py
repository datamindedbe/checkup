import os

from checkup import Context


conveyor_context = Context()
conveyor_context['api_key'] = os.environ['CHECKUP__CONVEYOR__API_KEY']
