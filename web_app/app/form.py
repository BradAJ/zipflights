from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, IntegerField, RadioField, SelectField
from wtforms.validators import Required, NumberRange


class FlyForm(Form):
    origin = TextField('origin', validators = [Required()])

class ITAForm(Form):
    
    duration = IntegerField('duration', validators = [Required(), NumberRange(min = 0, max = 300)])
    #month = IntegerField('month', validators = [Required(), NumberRange(min = 1, max = 12)])
    month = SelectField('month')
    
    destination = RadioField('destination', validators = [Required()])

class NonStopForm(Form):
    origin = TextField('origin', validators = [Required()])
    destination = TextField('destination', validators = [Required()])
    depart_year = IntegerField('depart_year', validators = [Required(), NumberRange(min = 2014, max = 2020)], default = 2014)
    return_year = IntegerField('return_year', validators = [Required(), NumberRange(min = 2014, max = 2020)], default = 2014)
    #depart_month = IntegerField('return_month', validators = [Required(), NumberRange(min = 1, max = 12)])
    #return_month = IntegerField('return_month', validators = [Required(), NumberRange(min = 1, max = 12)])
    depart_day = IntegerField('depart_day', validators = [Required(), NumberRange(min = 1, max = 31)])
    return_day = IntegerField('return_day', validators = [Required(), NumberRange(min = 1, max = 31)])

    depart_month = SelectField('depart_month')
    return_month = SelectField('return_month')