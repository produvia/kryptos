
export default [
  {
    path: '/',
    component: () => import('layouts/default'),
    children: [
      { path: '', component: () => import('pages/index') },
      { path: 'build', component: () => import('pages/buildStrategy') },
      { path: 'monitor/:stratId', component: () => import('pages/monitor'), props: true }
    ]
  },

  { // Always leave this as last one
    path: '*',
    component: () => import('pages/404')
  }
]
