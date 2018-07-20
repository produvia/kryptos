<template>
  <q-page padding>
    <div class="row">
      <h1 class="q-title">Strategy Overview</h1>
    </div>
        <q-card>
          <q-card-title>
            Info
          </q-card-title>
          <q-card-main>
            <q-list>
              <q-item>
                <q-item-side>
                  ID:
                </q-item-side>
                <q-item-main>
                  {{stratId}}
                </q-item-main>
              </q-item>
              <q-item>
                <q-item-side>
                  status:
                </q-item-side>
                <q-item-main>
                  {{stratInfo.status}}
                </q-item-main>
              </q-item>
              <q-item>
                <q-item-side>
                  Job Started at:
                </q-item-side>
                <q-item-main>
                  {{stratInfo.started_at}}
                </q-item-main>
              </q-item>
              <q-item>
                <q-item-side>
                  output:
                </q-item-side>
                <q-item-main>
                  <pre>{{stratInfo.meta}}</pre>
                </q-item-main>
              </q-item>
              <q-item>
                <q-item-side>
                  Result:
                </q-item-side>
                <q-item-main>
                  {{stratInfo.result}}
                </q-item-main>
              </q-item>
            </q-list>
          </q-card-main>
        </q-card>
    <!-- </div> -->
  </q-page>
</template>

<script>
import axios from 'axios'
export default {
  name: 'monitor',
  props: ['stratId'],
  data () {
    return {
      stratInfo: {}
    }
  },
  mounted () {
    const path = process.env.API_URL + 'monitor'
    let stratid = this.stratId
    axios.get(path, {
      crossdomain: true,
      params: {
        strat_id: stratid,
        queue_name: 'backtest'
      }
    })
      .then(response => {
        this.stratInfo = response.data.strat_info
        console.log(response)
      })
      .catch(error => {
        console.log(error)
      })
  }

}
</script>

<style>
</style>
