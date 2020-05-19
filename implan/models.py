from django.db import models
from django.contrib.auth.models import User
from django.db.models import signals
from functools import partial
from django.utils import timezone
from math import ceil

from datetime import datetime, timedelta

def calculate_dates(start_date, duration):
    end_date = start_date
    while duration > 1:
        end_date = end_date + timedelta(1)
        if end_date.weekday() < 5:
            duration -= 1
    return end_date

def calculate_task(minutes, fte, eff):
    day = 8*60
    duration = int(ceil(minutes / fte / eff / day))
    loading = minutes / eff / fte / duration / day
    return duration, loading

class AuditedModel(models.Model):
    created_by = models.ForeignKey(User, related_name='+', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(User, related_name='+', on_delete=models.CASCADE)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class PhaseModel(AuditedModel):
    class Meta:
        abstract = True
    ee_multipler = models.FloatField(default=2, verbose_name='EE Efficiency')
    ee_rate = models.FloatField(default=250, verbose_name='EE Rate')
    ee_fte = models.FloatField(default=0, verbose_name='EE FTEs')
    user_fte = models.FloatField(default=1, verbose_name='User FTEs')

    def is_ee(self): return self.ee_fte > 0.01
    def get_phase_task_value(self):
        fields = self.outline.split('.')
        phase, task = int(fields[0]), 0 if len(fields) == 1 else int(fields[1])
        return 10000*phase + task

    def generate_task(self, phase, order, start_date, pred, time = None, duration = None, suborder = None, title = 'Untitled Task', is_ee = True):

        # initial computations
        # who is the lead
        lead = 'Energy Exemplar' if self.ee_fte > self.user_fte or is_ee else self.implan.group.company.name
        
        # what is the total efficiency of all fte
        eff = self.ee_multipler if is_ee else ((self.ee_multipler*self.ee_fte + self.user_fte)/(self.ee_fte+self.user_fte))

        # what is the total number of all fte
        fte = (1 if self.ee_fte == 0 else self.ee_fte) if is_ee else (self.ee_fte + self.user_fte)

        # which resources are available
        res = dict()
        if is_ee or self.ee_fte > 0: res['1'] = 'Energy Exemplar'
        if self.user_fte > 0 and not is_ee: res['0'] = self.implan.group.company.name

        # compute task duration and available fte loading rate
        if duration is None:
            duration, loading = calculate_task(time, fte, eff)
        else:
            loading = 1

        # begin
        t = Task()
        t.implan = self.implan
        t.order = order
        t.name = title
        t.start_date = start_date
        t.cost = duration * 8 * loading * self.ee_rate * self.ee_fte
        t.end_date = calculate_dates(start_date, duration)
        t.duration = duration
        t.coord = lead
        t.pred = pred
        if phase is None:
            t.outline = '{:03}'.format(order)
        elif suborder is None:
            t.outline = '{:03}'.format(phase)
        else:
            t.outline = '{:03}.{:04}'.format(phase, suborder)
            suborder += 1
        t.res = ';'.join([v for v in res.values()])
        t.assign = ';'.join(['{}:{}'.format(k, 100 * loading * (self.ee_fte if k == '1' else self.user_fte)) for k in res.keys()])
        t.save()

        # post task updates
        start_date = t.end_date + timedelta(1)
        pred = str(order)
        order += 1

        return order, start_date, pred, suborder

    
def add_audit_fields(request, sender, instance=None, **kwargs):
    """
    Update the fields created_by and updated_by

    expected to be called in pre_save so instance save fields itself
    """
    if issubclass(sender, AuditedModel):
        if not instance.id:
            instance.created_by = request.user
        instance.modified_by = request.user


class AuditingMiddleWare:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        signals.pre_save.connect(partial(add_audit_fields, request), dispatch_uid=(self.__class__, request), weak=False)
        try:
            response = self.get_response(request)
        finally:
            signals.pre_save.disconnect(dispatch_uid=(self.__class__, request))

        return response
    
class Task(models.Model):
    implan = models.ForeignKey('ImplementationPlan', default=None, on_delete=models.CASCADE)
    order = models.IntegerField(default=1)
    name = models.CharField(max_length=100, default='Test')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(default=timezone.now)
    duration = models.IntegerField(default=1)
    completion = models.IntegerField(default=0)
    cost = models.FloatField(default=0.0)
    coord = models.CharField(max_length=100, default='')
    pred = models.CharField(max_length=100, default='')
    outline = models.CharField(max_length=100, default='')
    res = models.CharField(max_length=100, default='')
    assign = models.CharField(max_length=100, default='')

class Deployment(PhaseModel):
    implan = models.ForeignKey('ImplementationPlan', on_delete=models.CASCADE, default=0)
    install = models.BooleanField(verbose_name='Installation and Licensing', default=False)
    volume = models.IntegerField(verbose_name='Number of Desktops', default=0)
    cw = models.BooleanField(verbose_name='Cloud Workspaces', default=False)
    sql = models.BooleanField(verbose_name='Aurora SQL Server', default=False)
    gurobi = models.BooleanField(verbose_name='Aurora Gurobi', default=False)
    vpc = models.BooleanField(verbose_name='Virtual Private Cloud', default=False)
    connect = models.BooleanField(verbose_name='PLEXOS Connect', default=False)
    cc = models.BooleanField(verbose_name='PLEXOS Cloud Connect', default=False)
    multi = models.IntegerField(verbose_name='Multiple Environments e.g., DEV, TEST, PROD', default=0)
    non_standard = models.BooleanField(verbose_name='Non-standard Deployment', default=False)

    def __str__(self): return '{} Deployment {}'.format(self.implan.project_name, self.id)

    def generate_tasks(self, phase, order, start_date, pred):
        '''
        Generate Task objects related to this model object
        '''
        init = dict(order=order, start_date=start_date, pred=pred, phase=phase)
        suborder = 1
        is_tasks = False
        #phase_duration = 0.0

        if self.vpc and self.multi > 0:
            is_tasks = True
            time = 240 * self.multi * (3 if self.non_standard else 1)
            order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time=time, suborder=suborder, title='Virtual Private Cloud Setup', is_ee = False)

        if self.connect and self.multi > 0:
            is_tasks = True
            time = 240 * self.multi * (2 if self.vpc else 1) * (3 if self.non_standard else 1)
            order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time=time, suborder=suborder, title='Connect Installation')

        if self.sql and self.multi > 0:
            is_tasks = True
            time = 240 * self.multi * (2 if self.vpc else 1) * (3 if self.non_standard else 1)
            order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time=time, suborder=suborder, title='Aurora SQL Server Setup', is_ee = False)

        # install task
        if self.install:
            is_tasks = True
            order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time=12*self.volume, suborder=suborder, title='Desktop Installation')

        y1, y2 = start_date, start_date
        if self.cc:
            is_tasks = True
            order, x, y, z = self.generate_task(phase, order, init['start_date'], init['pred'], time=60, suborder=suborder, title = 'PLEXOS Cloud Connect')

        if self.cw:
            is_tasks = True
            order, x, y, z = self.generate_task(phase, order, init['start_date'], init['pred'], time=60 * self.volume, suborder=suborder, title = 'Cloud Workspace')

        if is_tasks: 
            t = Task()
            '''
            cost = models.FloatField(default=0.0)
            coord = models.CharField(max_length=100, default='')
            pred = models.CharField(max_length=100, default='')
            outline = models.CharField(max_length=100, default='')
            res = models.CharField(max_length=100, default='')
            assign = models.CharField(max_length=100, default='')
            '''
            t.implan = self.implan
            t.order = order
            order += 1
            t.name = 'Deployment'
            t.start_date = init['start_date']
            t.end_date = max(start_date, y1, y2)
            t.duration = (t.end_date - t.start_date).days + 1
            t.cost = (t.duration * 8 * 0.05 * self.ee_rate) if self.is_ee() else 0.0
            t.coord = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
            t.pred = init['pred']
            t.outline = '{:03}'.format(phase)
            t.res = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
            t.assign = '{}:{}'.format(1 if self.is_ee() else 0, 5.0)
            t.save()

        return phase + 1, order, start_date, pred

class Customization(PhaseModel):
    implan = models.ForeignKey('ImplementationPlan', on_delete=models.CASCADE, default=0)
    screens = models.IntegerField(verbose_name='Number of Custom Screens', default=0)
    description = models.TextField(verbose_name='Description of custom screens', default='')
    def __str__(self): return '{} Customization {}'.format(self.implan.project_name, self.id)
    def generate_tasks(self, phase, order, start_date, pred):
        '''
        Generate Task objects related to this model object
        '''
        init = dict(order=order, start_date=start_date, pred=pred, phase=phase)
        suborder = 1
        is_tasks = False
        #phase_duration = 0.0

        if self.screens > 0:
            is_tasks = True
            time = 80 * 60 * self.screens
            order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time, suborder=suborder, title='Custom Screens ({})'.format(self.screens))

        if is_tasks: 
            t = Task()
            '''
            cost = models.FloatField(default=0.0)
            coord = models.CharField(max_length=100, default='')
            pred = models.CharField(max_length=100, default='')
            outline = models.CharField(max_length=100, default='')
            res = models.CharField(max_length=100, default='')
            assign = models.CharField(max_length=100, default='')
            '''
            t.implan = self.implan
            t.order = order
            order += 1
            t.name = 'Customization'
            t.start_date = init['start_date']
            t.end_date = start_date - timedelta(1)
            t.duration = (t.end_date - t.start_date).days + 1
            t.cost = (t.duration * 8 * 0.05 * self.ee_rate) if self.is_ee() else 0.0
            t.coord = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
            t.pred = init['pred']
            t.outline = '{:03}'.format(phase)
            t.res = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
            t.assign = '{}:{}'.format(1 if self.is_ee() else 0, 5.0)
            t.save()

        return phase + 1, order, start_date, pred



class CommercialDatasets(AuditedModel):
    name = models.CharField(max_length=100, verbose_name='Commercial Dataset Name')
    is_nodal = models.BooleanField(verbose_name='Is it Nodal?', default=False)
    def __str__(self): return self.name

class ModelBuilding(PhaseModel):
    implan = models.ForeignKey('ImplementationPlan', on_delete=models.CASCADE, default=0)
    name = models.CharField(max_length=100, verbose_name='Name of Dataset', default='', blank=True)
    data = models.ForeignKey('CommercialDatasets', on_delete=models.CASCADE, verbose_name = 'Commercial Datasets', blank = True, null = True)
    carveouts = models.IntegerField(verbose_name='# of Carveouts', default = 0)
    difficulty = models.IntegerField(verbose_name='Complexity (1=Low, 5=High)', default=3)
    description = models.CharField(max_length=200, verbose_name='Brief Description', default='', blank=True)
    attr = models.IntegerField(verbose_name='Number of Benchmarks', default = 3)
    prec = models.IntegerField(verbose_name='Calibration Precision (1 to 5)', default = 1)
    def __str__(self): return '{} ModelBuilding {}'.format(self.implan.project_name, self.id)

    def generate_tasks(self, phase, order, start_date, pred):
        '''
        Generate Task objects related to this model object
        '''
        init = dict(order=order, start_date=start_date, pred=pred, phase=phase)
        suborder = 1
        is_tasks = False
        #phase_duration = 0.0

        '''
        name = models.CharField(max_length=100, verbose_name='Name of Dataset', default='')
        data = models.ForeignKey('CommercialDatasets', on_delete=models.CASCADE, verbose_name = 'Commercial Datasets', blank = True, default = None)
        carveouts = models.IntegerField(verbose_name='# of Carveouts', default = 0)
        difficulty = models.IntegerField(verbose_name='Complexity (1=Low, 5=High)', default=3)
        description = models.CharField(max_length=200, verbose_name='Brief Description', default='')
        attr = models.IntegerField(verbose_name='Number of Benchmarks', default = 3)
        prec = models.IntegerField(verbose_name='Calibration Precision (1 to 5)', default = 1)
        difficulty = models.IntegerField(verbose_name='Calibration Difficulty (1 to 5)', default = 1)
        '''
        
        # COTS data
        if not self.data is None:

            # updates
            if self.difficulty > 0:
                is_tasks = True
                time = 8 * 2 * 60 * (self.difficulty ** 2)
                order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time, suborder=suborder, title='Dataset Updates')

            # carveouts
            if self.carveouts > 0:
                is_tasks = True
                time = self.carveouts * 3 * 8 * 60 * (10 if self.data.is_nodal else 1)
                order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time, suborder=suborder, title='Carveouts ({})'.format(self.carveouts))

            # benchmarking
            if self.attr > 0:
                is_tasks = True
                time = (self.carveouts + 1) * (self.attr) * 3 * 8 * 60
                order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time, suborder=suborder, title='Benchmarking')

            # calibration
            if self.prec > 0:
                is_tasks = True
                time = (self.carveouts + 1) * (self.prec ** 2) * 5 * 8 * 60
                order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time, suborder=suborder, title='Calibration')

        # Bespoke data
        else:

            # model building
            if self.difficulty > 0:
                is_tasks = True
                time = 8 * 5 * 60 * (self.difficulty)
                order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time, suborder=suborder, title='Dataset Construction')

            # benchmarking
            if self.attr > 0:
                is_tasks = True
                time = (self.attr) * 3 * 8 * 60
                order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time, suborder=suborder, title='Benchmarking')

            # calibration
            if self.prec > 0:
                is_tasks = True
                time = (self.carveouts + 1) * (self.prec ** 2) * 5 * 8 * 60
                order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time, suborder=suborder, title='Calibration')


        if is_tasks: 
            t = Task()
            t.implan = self.implan
            t.order = order
            order += 1
            t.name = self.name if self.data is None else self.data.name
            t.start_date = init['start_date']
            t.end_date = start_date - timedelta(1)
            t.duration = (t.end_date - t.start_date).days + 1
            t.cost = (t.duration * 8 * 0.05 * self.ee_rate) if self.is_ee() else 0.0
            t.coord = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
            t.pred = init['pred']
            t.outline = '{:03}'.format(phase)
            t.res = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
            t.assign = '{}:{}'.format(1 if self.is_ee() else 0, 5.0)
            t.save()

        return phase + 1, order, start_date, pred


class Automation(PhaseModel):
    implan = models.ForeignKey('ImplementationPlan', on_delete=models.CASCADE, default=0)
    name = models.CharField(max_length=100, verbose_name='Automation Task', default='')
    inputs = models.IntegerField(verbose_name='Number of Inputs', default = 0)
    execute = models.IntegerField(verbose_name='Number of Executions', default = 0)
    reports = models.IntegerField(verbose_name='Number of Reports', default = 1)
    difficulty = models.IntegerField(verbose_name='Difficulty (1 to 5)', default=1)
    def __str__(self): return '{} Automation {}'.format(self.implan.project_name, self.id)

    def generate_tasks(self, phase, order, start_date, pred):
        '''
        Generate Task objects related to this model object
        '''
        init = dict(order=order, start_date=start_date, pred=pred, phase=phase)
        suborder = 1
        is_tasks = False
        #phase_duration = 0.0

        '''
        inputs = models.IntegerField(verbose_name='Number of Inputs', default = 0)
        execute = models.IntegerField(verbose_name='Number of Executions', default = 0)
        reports = models.IntegerField(verbose_name='Number of Reports', default = 1)
        difficulty = models.IntegerField(verbose_name='Difficulty (1 to 5)', default=1)
        '''
        
        if self.inputs > 0:
            is_tasks = True
            time = 8 * 60 * self.inputs * (self.difficulty ** 2)
            order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time, suborder=suborder, title='Input Automation')

        if self.execute > 0:
            is_tasks = True
            time = 4 * 60 * self.execute
            order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time, suborder=suborder, title='Execute Automation')

        if self.reports > 0:
            is_tasks = True
            time = 8 * 60 * self.reports * (self.difficulty ** 2)
            order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time, suborder=suborder, title='Custom Reports')

        if is_tasks: 
            t = Task()
            t.implan = self.implan
            t.order = order
            order += 1
            t.name = 'Automation ({})'.format(phase)
            t.start_date = init['start_date']
            t.end_date = start_date - timedelta(1)
            t.duration = (t.end_date - t.start_date).days + 1
            t.cost = (t.duration * 8 * 0.05 * self.ee_rate) if self.is_ee() else 0.0
            t.coord = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
            t.pred = init['pred']
            t.outline = '{:03}'.format(phase)
            t.res = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
            t.assign = '{}:{}'.format(1 if self.is_ee() else 0, 5.0)
            t.save()

        return phase + 1, order, start_date, pred

class SystemIntegration(PhaseModel):
    implan = models.ForeignKey('ImplementationPlan', on_delete=models.CASCADE, default=0)
    system_name = models.CharField(max_length=100, verbose_name='System Name', default = '')
    streams = models.IntegerField(verbose_name='Number of data streams', default = 1)
    method = models.CharField(max_length=100, verbose_name='Method of Integration (DB, API, Text)', default = '')

    def generate_tasks(self, phase, order, start_date, pred):
        '''
        Generate Task objects related to this model object
        '''
        init = dict(order=order, start_date=start_date, pred=pred, phase=phase)
        suborder = 1
        is_tasks = False
        #phase_duration = 0.0

        '''
        system_name = models.CharField(max_length=100, verbose_name='System Name', default = '')
        streams = models.IntegerField(verbose_name='Number of data streams', default = 1)
        method = models.CharField(max_length=100, verbose_name='Method of Integration (DB, API, Text)', default = '')
        '''
        
        for i in range(self.streams):
            is_tasks = True
            if i == 0:
                order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time=40 * 60, suborder=suborder, title='Replicate ' + self.system_name)
            order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time=80*60, suborder=suborder, title='{} Data Stream ({})'.format(self.method, i + 1))

        if is_tasks: 
            t = Task()
            t.implan = self.implan
            t.order = order
            order += 1
            t.name = self.system_name
            t.start_date = init['start_date']
            t.end_date = start_date - timedelta(1)
            t.duration = (t.end_date - t.start_date).days + 1
            t.cost = (t.duration * 8 * 0.05 * self.ee_rate) if self.is_ee() else 0.0
            t.coord = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
            t.pred = init['pred']
            t.outline = '{:03}'.format(phase)
            t.res = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
            t.assign = '{}:{}'.format(1 if self.is_ee() else 0, 5.0)
            t.save()

        return phase + 1, order, start_date, pred

class ProductTraining(PhaseModel):
    implan = models.ForeignKey('ImplementationPlan', on_delete=models.CASCADE, default=0)
    desc = models.CharField(max_length=100, verbose_name='Description')
    urgent = models.BooleanField(verbose_name='Urgent Need', default=False)
    xPert = models.BooleanField(verbose_name='xPert only', default=False)
    basic = models.BooleanField(verbose_name='Basic Training', default=False)
    onsite = models.BooleanField(verbose_name='On-site Training', default=False)
    new_modelers = models.BooleanField(verbose_name='New to modeling?', default=False)
    advanced = models.BooleanField(verbose_name='Advanced/Customized Training', default=False)
    recent = models.BooleanField(verbose_name='Recent Training?', default=False)

    def generate_tasks(self, phase, order, start_date, pred):

        '''
        Generate Task objects related to this model object
        '''
        init = dict(order=order, start_date=start_date, pred=pred, phase=phase)
        suborder = 1
        is_tasks = False
        #phase_duration = 0.0

        '''
        desc = models.CharField(max_length=100, verbose_name='Description')
        urgent = models.BooleanField(verbose_name='Urgent Need', default=False)
        xPert = models.BooleanField(verbose_name='xPert only', default=False)
        basic = models.BooleanField(verbose_name='Basic Training', default=False)
        onsite = models.BooleanField(verbose_name='On-site Training', default=False)
        new_modelers = models.BooleanField(verbose_name='New to modeling?', default=False)
        advanced = models.BooleanField(verbose_name='Advanced/Customized Training', default=False)
        recent = models.BooleanField(verbose_name='Recent Training?', default=False)
        '''
        
        # updates
        if self.xPert:
            if self.basic:
                is_tasks = True
                time = 10 * 60 * (2 if self.new_modelers else 1) / (2 if self.recent else 1) / self.implan.company_FTE
                order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time, suborder=suborder, title='xPert Basic Training')

            if self.advanced:
                is_tasks = True
                time = 10 * 60 * (2 if self.new_modelers else 1) / (2 if self.recent else 1) / self.implan.company_FTE
                order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time, suborder=suborder, title='xPert Advanced Training')
        
        elif self.onsite:

            if self.basic:
                is_tasks = True
                duration = 2 * (1.5 if self.new_modelers else 1) / (2 if self.recent else 1) / self.implan.company_FTE
                order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time, suborder=suborder, title='Onsite Basic Training', is_ee = True)

            if self.advance:
                is_tasks = True
                duration = 2 * (1.5 if self.new_modelers else 1) / (2 if self.recent else 1) / self.implan.company_FTE
                order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time, suborder=suborder, title='Onsite Advanced Training', is_ee = True)

        else:

            if self.basic:
                is_tasks = True
                duration = 2 * (1.5 if self.new_modelers else 1) / (2 if self.recent else 1) / self.implan.company_FTE
                order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time, suborder=suborder, title='Webinar Basic Training', is_ee = True)

            if self.advance:
                is_tasks = True
                duration = 2 * (1.5 if self.new_modelers else 1) / (2 if self.recent else 1) / self.implan.company_FTE
                order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, time, suborder=suborder, title='Webinar Advanced Training', is_ee = True)
            
        if is_tasks: 
            t = Task()
            t.implan = self.implan
            t.order = order
            order += 1
            t.name = self.desc
            t.start_date = init['start_date']
            t.end_date = start_date - timedelta(1)
            t.duration = (t.end_date - t.start_date).days + 1
            t.cost = (t.duration * 8 * 0.05 * self.ee_rate) if self.is_ee() else 0.0
            t.coord = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
            t.pred = init['pred']
            t.outline = '{:03}'.format(phase)
            t.res = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
            t.assign = '{}:{}'.format(1 if self.is_ee() else 0, 5.0)
            t.save()

        return phase + 1, order, start_date, pred

class HandoverWorkshop(PhaseModel):
    implan = models.ForeignKey('ImplementationPlan', on_delete=models.CASCADE, default=0)
    purpose = models.CharField(max_length=100)
    days = models.FloatField(default=0.0)

    def generate_tasks(self, phase, order, start_date, pred):
        '''
        Generate Task objects related to this model object
        '''
        init = dict(order=order, start_date=start_date, pred=pred, phase=phase)
        suborder = 1
        is_tasks = False
        #phase_duration = 0.0

        '''
        purpose = models.CharField(max_length=100)
        days = models.FloatField(default=0.0)
        '''
        
        t = Task()
        t.implan = self.implan
        t.order = order
        t.name = self.purpose
        t.start_date = start_date
        t.end_date = calculate_dates(start_date, self.days)
        t.duration = (t.end_date - t.start_date).days + 1
        t.cost = (t.duration * 8 * self.ee_rate) if self.is_ee() else 0.0
        t.coord = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
        t.pred = init['pred']
        t.outline = '{:03}'.format(phase)
        t.res = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
        t.assign = '{}:{}'.format(1 if self.is_ee() else 0, 100.0)
        t.save()

        return phase + 1, order + 1, t.end_date + timedelta(1), order + 1

class DetailedPlanningPhase(PhaseModel):
    implan = models.ForeignKey('ImplementationPlan', on_delete=models.CASCADE, verbose_name = 'Implementation Plan')
    scope = models.IntegerField(verbose_name='Scope (days)', default = 0)
    spec = models.IntegerField(verbose_name='Specification (days)', default = 0)
    design = models.IntegerField(verbose_name='Design (days)', default = 0)
    quality = models.IntegerField(verbose_name='Quality Plan (days)', default = 0)

    def generate_tasks(self, phase, order, start_date, pred):

        '''
        Generate Task objects related to this model object
        '''
        init = dict(order=order, start_date=start_date, pred=pred, phase=phase)
        suborder = 1
        is_tasks = False
        #phase_duration = 0.0

        '''
        scope = models.IntegerField(verbose_name='Scope (days)', default = 0)
        spec = models.IntegerField(verbose_name='Specification (days)', default = 0)
        design = models.IntegerField(verbose_name='Design (days)', default = 0)
        quality = models.IntegerField(verbose_name='Quality Plan (days)', default = 0)
        '''
        
        # updates
        if self.scope > 0:
            is_tasks = True
            order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, duration=self.scope, suborder=suborder, title='Scoping', is_ee=True)
            
        # updates
        if self.spec > 0:
            is_tasks = True
            order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, duration=self.spec, suborder=suborder, title='Specifications', is_ee=True)

        # updates
        if self.design > 0:
            is_tasks = True
            order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, duration=self.updates, suborder=suborder, title='Design', is_ee=True)

        # updates
        if self.quality > 0:
            is_tasks = True
            order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, duration=self.quality, suborder=suborder, title='Quality Plan', is_ee=True)

        if is_tasks: 
            t = Task()
            t.implan = self.implan
            t.order = order
            order += 1
            t.name = 'Detailed Planning'
            t.start_date = init['start_date']
            t.end_date = start_date - timedelta(1)
            t.duration = (t.end_date - t.start_date).days + 1
            t.cost = (t.duration * 8 * 0.05 * self.ee_rate) if self.is_ee() else 0.0
            t.coord = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
            t.pred = init['pred']
            t.outline = '{:03}'.format(phase)
            t.res = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
            t.assign = '{}:{}'.format(1 if self.is_ee() else 0, 5.0)
            t.save()

        return phase + 1, order, start_date, pred

class Validation(PhaseModel):
    implan = models.ForeignKey('ImplementationPlan', on_delete=models.CASCADE, verbose_name = 'Implementation Plan')
    training = models.IntegerField(verbose_name='Implementation Training (days)', default = 0)
    accept = models.IntegerField(verbose_name='Functional Acceptance (days)', default = 0)
    test = models.IntegerField(verbose_name='Model Testing (days)', default = 0)
    integ = models.IntegerField(verbose_name='Integration Testing (days)', default = 0)

    def generate_tasks(self, phase, order, start_date, pred):

        '''
        Generate Task objects related to this model object
        '''
        init = dict(order=order, start_date=start_date, pred=pred, phase=phase)
        suborder = 1
        is_tasks = False
        #phase_duration = 0.0

        '''
        training = models.IntegerField(verbose_name='Implementation Training (days)', default = 0)
        accept = models.IntegerField(verbose_name='Functional Acceptance (days)', default = 0)
        test = models.IntegerField(verbose_name='Model Testing (days)', days = 0)
        integ = models.IntegerField(verbose_name='Integration Testing (days)', days = 0)
        '''
        
        # updates
        if self.training > 0:
            is_tasks = True
            order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, duration=self.training, suborder=suborder, title='Implementation Training', is_ee=True)
            
        # updates
        if self.accept > 0:
            is_tasks = True
            order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, duration=self.accept, suborder=suborder, title='Functional Testing', is_ee=True)

        # updates
        if self.test > 0:
            is_tasks = True
            time = 8 * 60 * self.test / self.implan.ee_FTE
            order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, duration=self.test, suborder=suborder, title='Model Testing', is_ee=True)

        # updates
        if self.integ > 0:
            is_tasks = True
            time = 8 * 60 * self.integ / self.implan.ee_FTE
            order, start_date, pred, suborder = self.generate_task(phase, order, start_date, pred, duration=self.integ, suborder=suborder, title='Integration Testing', is_ee=True)

        if is_tasks: 
            t = Task()
            t.implan = self.implan
            t.order = order
            order += 1
            t.name = 'Validation'
            t.start_date = init['start_date']
            t.end_date = start_date - timedelta(1)
            t.duration = (t.end_date - t.start_date).days + 1
            t.cost = (t.duration * 8 * 0.05 * self.ee_rate) if self.is_ee() else 0.0
            t.coord = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
            t.pred = init['pred']
            t.outline = '{:03}'.format(phase)
            t.res = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
            t.assign = '{}:{}'.format(1 if self.is_ee() else 0, 5.0)
            t.save()

        return phase + 1, order, start_date, pred

class GoLive(PhaseModel):
    implan = models.ForeignKey('ImplementationPlan', on_delete=models.CASCADE, verbose_name = 'Implementation Plan')
    days = models.IntegerField(verbose_name='Go-live support (days)')

    def generate_tasks(self, phase, order, start_date, pred):
        '''
        Generate Task objects related to this model object
        '''
        init = dict(order=order, start_date=start_date, pred=pred, phase=phase)
        suborder = 1
        is_tasks = False
        #phase_duration = 0.0

        '''
        purpose = models.CharField(max_length=100)
        days = models.FloatField(default=0.0)
        '''
        
        t = Task()
        t.implan = self.implan
        t.order = order
        t.name = 'Go-Live Support'
        t.start_date = start_date
        t.end_date = calculate_dates(start_date, self.days)
        t.duration = (t.end_date - t.start_date).days + 1
        t.cost = (t.duration * 8 * self.ee_rate) if self.is_ee() else 0.0
        t.coord = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
        t.pred = init['pred']
        t.outline = '{:03}'.format(phase)
        t.res = 'Energy Exemplar' if self.is_ee() else self.implan.group.company.name
        t.assign = '{}:{}'.format(1 if self.is_ee() else 0, 100.0)
        t.save()

        return phase + 1, order + 1, t.end_date + timedelta(1), order + 1

class TechnicalDifferentiators(AuditedModel):
    name = models.CharField(max_length=100)
    def __str__(self): return self.name

class UniqueBusinessValueDriver(AuditedModel):
    name = models.CharField(max_length=100, verbose_name='Value Driver')
    bene = models.TextField(max_length=400, verbose_name='Benefit Statement')
    valu = models.TextField(max_length=1000, verbose_name='Value Proposition')
    tech = models.ManyToManyField(TechnicalDifferentiators, verbose_name = 'Technical Differentiators')
    def __str__(self): return self.name

class UseCase(AuditedModel):
    name = models.CharField(max_length=100, verbose_name='Use Case Name')
    description = models.TextField(max_length=400, verbose_name='Use Case Description')
    ubv = models.ManyToManyField(UniqueBusinessValueDriver, verbose_name='Unique Business Value')
    def __str__(self): return self.name

class Company(AuditedModel):
    name = models.CharField(max_length=100, verbose_name='Account Name')
    sfdc = models.CharField(max_length=400, verbose_name='Salesforce.com Link')
    def __str__(self): return self.name

class Group(AuditedModel):
    name = models.CharField(max_length=100, verbose_name='Department/Group Name')
    contact = models.CharField(max_length=100, verbose_name='Contact Name')
    company = models.ForeignKey(Company, verbose_name='Account Name', on_delete=models.CASCADE)
    def __str__(self): return '{} -- {}'.format(self.company, self.name)

# Create your models here
class ImplementationPlan(AuditedModel):
    project_name = models.CharField(max_length=100, default='')
    project_start = models.DateField(default=timezone.now)
    group = models.ForeignKey(Group, verbose_name='Department / Group', on_delete=models.CASCADE, default=0)
    usecase = models.ManyToManyField(UseCase, verbose_name='Use Cases')
    integration = models.TextField(verbose_name='System Integration Strategy')
    company_FTE = models.FloatField(verbose_name='Department Employee Resources', default=0.5)
    ee_FTE = models.FloatField(verbose_name='Energy Exemplar Resources', default=0.0)
    cons_FTE = models.FloatField(verbose_name='Consultant Resources', default=0.0)
    def __str__(self): return '{} -- {} {}'.format(self.project_name, self.group.company.name, self.group.name)
    def clear_tasks(self):
        Task.objects.filter(implan__id=self.id).delete()

    def compute_tasks(self):
        # deployment
        phase, order, start_date, pred, outline = 1, 1, self.project_start, '', 1
        for obj in Deployment.objects.filter(implan__id=self.id):
            phase, order, start_date, pred = obj.generate_tasks(phase, order, start_date, pred)

        # urgent training
        for obj in ProductTraining.objects.filter(implan__id=self.id, urgent=True):
            phase, order, start_date, pred = obj.generate_tasks(phase, order, start_date, pred)

        # detailed planning
        for obj in DetailedPlanningPhase.objects.filter(implan__id=self.id):
            phase, order, start_date, pred = obj.generate_tasks(phase, order, start_date, pred)        

        # model building
        for obj in ModelBuilding.objects.filter(implan__id=self.id):
            phase, order, start_date, pred = obj.generate_tasks(phase, order, start_date, pred)        

        # customization
        for obj in Customization.objects.filter(implan__id=self.id):
            phase, order, start_date, pred = obj.generate_tasks(phase, order, start_date, pred)

        # system integration
        for obj in SystemIntegration.objects.filter(implan__id=self.id):
            phase, order, start_date, pred = obj.generate_tasks(phase, order, start_date, pred)        

        # automation
        for obj in Automation.objects.filter(implan__id=self.id):
            phase, order, start_date, pred = obj.generate_tasks(phase, order, start_date, pred)        

        # validation
        for obj in Validation.objects.filter(implan__id=self.id):
            phase, order, start_date, pred = obj.generate_tasks(phase, order, start_date, pred)        

        # handover workshop
        for obj in HandoverWorkshop.objects.filter(implan__id=self.id):
            phase, order, start_date, pred = obj.generate_tasks(phase, order, start_date, pred)        

        # golive
        for obj in GoLive.objects.filter(implan__id=self.id):
            phase, order, start_date, pred = obj.generate_tasks(phase, order, start_date, pred)        

        # non urgent training
        for obj in ProductTraining.objects.filter(implan__id=self.id, urgent=False):
            phase, order, start_date, pred = obj.generate_tasks(phase, order, start_date, pred)        

    def get_tasks(self):
        return Task.objects.filter(implan__id=self.id).order_by('outline')

def add_task_objects(request, sender, instance=None, **kwargs):
    """
    create task objects related to a saved ImplementationPlan
    """
    if issubclass(sender, ImplementationPlan):
        instance.clear_tasks()
        instance.compute_tasks()

class TaskMiddleWare:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        signals.post_save.connect(partial(add_task_objects, request), dispatch_uid=(self.__class__, request), weak=False)
        try:
            response = self.get_response(request)
        finally:
            signals.pre_save.disconnect(dispatch_uid=(self.__class__, request))

        return response
    
