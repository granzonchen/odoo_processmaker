from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError, UserError
import time


class ProcessStart(models.TransientModel):
    _name = 'pm.process_start'
    _description = "Process Start Wizard "

    name = fields.Char('Name', required=True)
    detail = fields.Html('Case Detail')
    user_id = fields.Many2one(
        'res.users', string='User', default=lambda self: self.env.user)
    parent_task_id = fields.Many2one(
        'syd_bpm.task_executed', string="Parent Task Executed")
    parent_del_index = fields.Integer('Parent Del Index')

    def start_process(self):
        context = dict(self.sudo()._context or {})
        active_ids = context.get('active_ids', []) or []
        for process in self.sudo().env['syd_bpm.process'].browse(active_ids):
            self.process_start(process)
        return {'type': 'ir.actions.act_window_close'}

    def _val_case(self, case, process):
        self.ensure_one()
        val = {
            'name': self.name,
            'process_id': process.id,
            'detail': self.detail,
            'description': process.description,
            'user_id': self.user_id.id,
            'parent_task_id': self.parent_task_id.id,
            'pm_case_id': case['app_uid']
        }
        val['parent_del_index'] = self.parent_del_index
        return val

    def _val_task_executed(self, task, case_id):
        self.ensure_one()
        activity_id = self.env['syd_bpm.activity'].search(
            [('pm_activity_id', '=', task['tas_uid'])])
        val = {
            'name': task['tas_title'],
            'is_task_active': True,
            'case_id': case_id.id,
            'date_task_start': fields.Datetime.now(),
            'pm_task_id': task['tas_uid'],
            'pm_del_index': task['del_index'],
            'activity_id': activity_id.id
        }
        return val

    def _val_object(self, vid, case_id):
        self.ensure_one()
        val = {
            'name': vid.name,
            'process_object_id': vid.id,
            'case_id': case_id.id
        }
        return val

    def process_start(self, process):
        if (not process.startable):
            raise ValidationError('Process not startable')
        act_id = self.sudo().env['syd_bpm.activity'].search(
            [('process_id', '=', process.id), ('is_start_activity', '=', True)], limit=1)
        case = process.sudo().process_group_id.start_process(process, act_id)
        case_id = self.sudo().env['syd_bpm.case'].create(
            self._val_case(case, process))
        current_tasks = process.process_group_id._get_current_tasks(case)
        for task in current_tasks:
            self.sudo().env['syd_bpm.task_executed'].create(
                self._val_task_executed(task, case_id))
        return case_id

    def trigger_process(self, process, record):
        if (not process.startable):
            raise ValidationError('Process not startable')
        act_id = self.sudo().env['syd_bpm.activity'].search(
            [('process_id', '=', process.id), ('is_start_activity', '=', True)], limit=1)
        case = process.sudo().process_group_id.start_process(process, act_id)
        case_id = self.sudo().env['syd_bpm.case'].create(
            self._val_case(case, process))
        current_tasks = process.process_group_id._get_current_tasks(case)
        for task in current_tasks:
            self.sudo().env['syd_bpm.task_executed'].create(
                self._val_task_executed(task, case_id))
        return case_id
