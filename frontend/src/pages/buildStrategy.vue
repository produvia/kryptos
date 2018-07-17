<template>
  <q-page padding>
  <div class="row">
    <q-card glossy class="col">
    <q-card-title class='bg-primary text-white'>
      Basic Configuration
    </q-card-title>
    <q-card-separator />
    <q-card-main>
      <q-field helper='Strategy Name'>
          <q-input v-model='form.name'/>
      </q-field>

      <q-field helper='Trade Type'>
        <q-select placeholder='backtest'
         v-model='form.trade_type'
         :options='tradeTypes'/>
      </q-field>

      <q-field helper='Exchange'>
        <q-select  placeholder='form.exchange'
         v-model='form.exchange'
         :options='exchanges'/>
      </q-field>

      <q-field helper='Start Date'>
        <q-datetime v-model='form.start' type='date' default-value='form.start'/>
      </q-field>

      <q-field helper='End Date'>
        <q-datetime v-model='form.end' type='date' default-value='form.end'/>
      </q-field>

      <q-field helper='Base Currency'>
          <q-input v-model='form.base_currency'  placeholder='form.base_currency'/>
      </q-field>

      <q-field helper='Asset'>
          <q-input v-model='form.asset'  placeholder='form.trade_type'/>
      </q-field>

      <q-field helper='Data Frequency'>
          <q-select
           v-model='form.data_freq'
           :options='dataFrequencies'/>
      </q-field>

      <q-field helper='History Frequency'>
          <q-select
           v-model='form.history_freq'
           :options='historyFrequencies'/>
      </q-field>

      <q-field helper='Bar Period'>
          <q-input v-model='form.bar_period' type='number'  placeholder='form.trade_type'/>
      </q-field>

      <q-field helper='Capital Base'>
          <q-input v-model='form.capital_base' type='number'  placeholder='form.trade_type'/>
      </q-field>

      <q-field helper='Order Size'>
          <q-input v-model='form.order_size' type='number'  placeholder='form.trade_type'/>
      </q-field>

      <q-field helper='Slippage Allowed'>
          <q-input v-model='form.slippage_allowed' type='number'  placeholder='form.trade_type'/>
      </q-field>

      <q-btn color='primary' @click='submit'>Submit</q-btn>

    </q-card-main>
    </q-card>

    <q-card class="col">
      <q-card-title></q-card-title>
    </q-card>
  </div>
  </q-page>
</template>

<script>
import axios from 'axios'
export default {
  name: 'BuildStrategy',
  data () {
    return {
      stratID: null,
      form: {
        name: null,
        trade_type: 'daily',
        start: '2017-10-10',
        end: '2018-3-28',
        base_currency: 'usd',
        asset: 'btc',
        data_freq: 'daily',
        history_freq: '1d',
        exchange: 'bittrex',
        capital_base: 5000,
        bar_period: 50,
        oerder_size: 0.5,
        slippage_allowed: 0.05
      },
      exchanges: [
        {
          label: 'bitfinex',
          value: 'bitfinex'
        },
        {
          label: 'poloniex',
          value: 'poloniex'
        },
        {
          label: 'bittrex',
          value: 'bittrex'
        }
      ],
      tradeTypes: [
        {
          label: 'backtest',
          value: 'backtest'
        },
        {
          label: 'paper',
          value: 'paper'
        },
        {
          label: 'live',
          value: 'live'
        }
      ],
      dataFrequencies: [
        {
          label: 'minute',
          value: 'minute'
        },
        {
          label: 'daily',
          value: 'daily'
        }
      ],
      historyFrequencies: [
        {
          label: 'minute (1T)',
          value: '1T'
        },
        {
          label: 'daily (1d)',
          value: '1d'
        }
      ]
    }
  },
  methods: {
    submit () {
      console.log('Submitting strategy')
      const path = 'http://0.0.0.0:5000/api/submit'
      axios.post(path, this.form, {crossdomain: true})
        .then(response => {
          this.stratId = response.data.job_id
          console.log(response)
          this.$router.push('monitor/' + this.stratId)
        })
        .catch(error => {
          console.log(error)
        })
    }
  }

}
</script>

<style>
</style>
