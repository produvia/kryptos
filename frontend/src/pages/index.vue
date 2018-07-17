<template>
  <q-page class="flex flex-center">
    <img alt="Quasar logo" src="~assets/kryptos-banner.jpg">

    <div class="row">
      <q-card color='secondary'>
        <q-card-title>
          Join the Financial Revolution Today
        </q-card-title>
        <q-card-actions>
          <q-btn color='tertiary' @click="$router.push('/build')">
            Build A Strategy
          </q-btn>
          <q-btn color='tertiary'>
            Get Authorized to begin trading
          </q-btn>
        </q-card-actions>
      </q-card>
    </div>

  </q-page>
</template>

<style>
</style>

<script>
export default {
  name: 'PageIndex'
}
</script>
