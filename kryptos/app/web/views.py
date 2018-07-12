# -*- coding: utf-8 -*-
"""Public section, including homepage and signup."""

import json
from flask import Blueprint, Response, render_template, flash, url_for, request, redirect
import redis
from rq import Queue, Connection

from kryptos.strategy import Strategy
from kryptos.app.extensions import jsonrpc
from kryptos.utils.outputs import in_docker
from kryptos.worker import worker
from kryptos.app.web.forms import TradeInfoForm

blueprint = Blueprint("public", __name__, template_folder='../templates', static_folder="../static")

@blueprint.route("/", methods=["GET", "POST"])
def home():
    """Landing page for the web/html blueprint"""
    return render_template('base.html', form=TradeInfoForm())

@blueprint.route("/submit", methods=['POST'])
def submit():
    form = TradeInfoForm()
    if form.validate_on_submit():

        strat_dict = {
           "EXCHANGE": form.exchange.data,
           "ASSET": form.asset.data,
           "DATA_FREQ": form.data_freq.data,
           "HISTORY_FREQ": form.history_freq.data,
           "CAPITAL_BASE": form.capital_base.data,
           "BASE_CURRENCY": form.base_currency.data,
           "START": form.start.data,
           "END": form.end.data,
           "BARS": form.bar_period.data,
           "ORDER_SIZE": form.order_size.data,
           "SLIPPAGE_ALLOWED": form.slippage_allowed.data

        }
        live = form.trade_type in ['live', 'paper']
        simulate_orders = form.trade_type == 'live'

        job_id, queue_name = worker.queue_strat(json.dumps(strat_dict), live, simulate_orders)
        flash('Strategy Queued!')
        # return render_template('strat_page.html', strat_id=job_id)
        # return redirect(url_for('status'), strat_id=job_id)
        return poll_status(job_id, queue_name)

    return 'Failed {}'.format(form.errors)


@blueprint.route("/status")
def poll_status(strat_id, queue_name):
    # strat_id = request.args.get("strat_id")
    q = worker.get_queue(queue_name)
    job = q.fetch_job(strat_id)

    def generate():
        while not job.is_finished:
            yield json.dumps(job.meta) + '\n'
        return json.dumps(job.result)
    return Response(generate(), mimetype='text/html')
