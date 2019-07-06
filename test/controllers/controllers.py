# -*- coding: utf-8 -*-
from odoo import http
from openerp import tools
from openerp.http import request
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug
from openerp.addons.website.controllers import main
import werkzeug
from odoo import models, fields, api
import base64
import json

from openerp import SUPERUSER_ID

class Test(http.Controller):

    @api.multi
    def get_values(self):
        news = request.env['eufonews'].search([('publish','=',True)])
        news_lines = []
        for line in news:
            news_lines.append((line.date,line.news))
        values = {
            'news': news_lines,
        }
        return values

    @http.route([
        '/works',
        '/works/country/<model("res.country"):country>',
        '/works/department/<model("hr.department"):department>',
        '/works/country/<model("res.country"):country>/department/<model("hr.department"):department>',
        '/works/office/<int:office_id>',
        '/works/country/<model("res.country"):country>/office/<int:office_id>',
        '/works/department/<model("hr.department"):department>/office/<int:office_id>',
        '/works/country/<model("res.country"):country>/department/<model("hr.department"):department>/office/<int:office_id>',
    ], type='http', auth="public", website=True)
    
    def jobs(self, country=None, department=None, office_id=None, **kwargs):
        env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))

        Country = env['res.country']
        Jobs = env['hr.job']

        # List jobs available to current UID
        job_ids = Jobs.search([], order="website_published desc,no_of_recruitment desc").ids
        # Browse jobs as superuser, because address is restricted
        jobs = Jobs.sudo().browse(job_ids)

        # Default search by user country
        if not (country or department or office_id or kwargs.get('all_countries')):
            country_code = request.session['geoip'].get('country_code')
            if country_code:
                countries_ = Country.search([('code', '=', country_code)])
                country = countries_[0] if countries_ else None
                if not any(j for j in jobs if j.address_id and j.address_id.country_id == country):
                    country = False

        # Filter job / office for country
        if country and not kwargs.get('all_countries'):
            jobs = [j for j in jobs if j.address_id is None or j.address_id.country_id and j.address_id.country_id.id == country.id]
            offices = set(j.address_id for j in jobs if j.address_id is None or j.address_id.country_id and j.address_id.country_id.id == country.id)
        else:
            offices = set(j.address_id for j in jobs if j.address_id)

        # Deduce departments and countries offices of those jobs
        departments = set(j.department_id for j in jobs if j.department_id)
        countries = set(o.country_id for o in offices if o.country_id)

        if department:
            jobs = (j for j in jobs if j.department_id and j.department_id.id == department.id)
        if office_id and office_id in map(lambda x: x.id, offices):
            jobs = (j for j in jobs if j.address_id and j.address_id.id == office_id)
        else:
            office_id = False
        # Render page
        return http.request.render("test.index", {
            'jobs': jobs,
            'countries': countries,
            'departments': departments,
            'offices': offices,
            'country_id': country,
            'department_id': department,
            'office_id': office_id,
            'news': self.get_values().get('news')
        })

    @http.route('/works/add', type='http', auth="user", website=True)
    def jobs_add(self, **kwargs):
        job = request.env['hr.job'].create({
            'name': _('Job Title'),
            'news': self.get_values().get('news')
        })
        return request.redirect("/works/detail/%s?enable_editor=1" % slug(job))

    @http.route('/works/detail/<model("hr.job"):job>', type='http', auth="public", website=True)
    def jobs_detail(self, job, **kwargs):
        return request.render("test.detail", {
            'job': job,
            'main_object': job,
            'news': self.get_values().get('news')
        })

    @http.route('/works/apply/<model("hr.job"):job>', type='http', auth="public", website=True)
    def jobs_apply(self, job, **kwargs):
        error = {}
        default = {}
        if 'website_hr_recruitment_error' in request.session:
            error = request.session.pop('website_hr_recruitment_error')
            default = request.session.pop('website_hr_recruitment_default')
        return request.render("test.apply", {
            'job': job,
            'error': error,
            'default': default,
            'news': self.get_values().get('news')
        })

    @http.route('/thankyou',auth="public")
    def thanks(self,**kw):
    	return http.request.render("test.bravo",{
    		'thankyou':['Bravo'],
    		})    	         

