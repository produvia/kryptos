import os
import json
from flask import send_file, Blueprint, redirect, current_app, render_template, request, url_for
from flask_user import current_user, login_required

from app.extensions import db
from app.forms.forms import UserExchangeKeysForm, TradeInfoForm
from kryptos.worker import worker

blueprint = Blueprint('account', __name__, url_prefix='/account')


@blueprint.route('/exchanges', methods=['GET', 'POST'])
@login_required
def manage_exchanges():
    form = UserExchangeKeysForm()

    # Process valid POST
    if request.method == 'POST' and form.validate():

        exchange_dict = {
            'name': form.exchange.data,
            'key': form.api_key.data,
            'secret': form.api_secret.data
        }

        base = 'catalyst/data/exchanges'
        exchange_dir = os.path.join(base, form.exchange.data)
        file_name = 'auth_' + str(current_user.id) + '.json'
        user_auth_file = os.path.join(exchange_dir, file_name)

        if not os.path.exists(exchange_dir):
            os.makedirs(exchange_dir)



        with open(user_auth_file, 'w') as f:
            current_app.logger.error(f'Writing to {user_auth_file}')
            json.dump(exchange_dict, f)


        return redirect(url_for('user.edit_user_profile'))

    return render_template('user/user_exchanges.html', form=form)
