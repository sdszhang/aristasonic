
class Airflow(object):
   UNKNOWN = 'unknown'
   EXHAUST = 'exhaust'
   INTAKE = 'intake'

   # TODO: deprecate and rename reverse/forward to exhaust/intake
   #       it is much more meaningful and in phase with the sonic platform api
   REVERSE = 'reverse'
   FORWARD = 'forward'
