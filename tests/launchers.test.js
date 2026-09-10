const assert = require('node:assert/strict')
const test = require('node:test')
const path = require('node:path')
const launcher = require('../pinokio.js')

function menu(installed, running = [], local = {}) {
  return launcher.menu({}, {
    exists: location => installed && location === 'app/env',
    running: script => running.includes(script),
    local: () => local,
  })
}

test('installation, launch and maintenance use the same environment', () => {
  for (const name of ['install', 'start', 'update']) {
    const step = require(`../${name}.js`).run.find(s => s.params.venv)
    assert.equal(path.posix.join(step.params.path, step.params.venv), 'app/env')
  }
  assert.equal(require('../reset.js').run[0].params.path, 'app/env')
  assert.equal(require('../link.js').run[0].params.venv, 'app/env')
})

test('menus reflect installation and server readiness', async () => {
  assert.equal((await menu(false))[0].href, 'install.js')
  assert.equal((await menu(true))[0].href, 'start.js')
  assert.equal((await menu(true, ['start.js']))[0].href, 'start.js')
  const ready = await menu(true, ['start.js'], { url: 'http://127.0.0.1:7861' })
  assert.equal(ready[0].href, 'http://127.0.0.1:7861')
  assert.equal(ready[0].default, true)
})

test('maintenance stays visible when the environment disappears', async () => {
  for (const script of ['install', 'reset', 'update', 'link']) {
    assert.equal((await menu(false, [`${script}.js`]))[0].href, `${script}.js`)
  }
})

test('start captures only the local URL from Gradio output', () => {
  const start = require('../start.js')
  const pattern = start.run[0].params.on[0].event
  const match = new RegExp(pattern.slice(1, -1)).exec('Running on local URL:  http://127.0.0.1:7861\u001b[0m')
  assert.equal(match[1], 'http://127.0.0.1:7861')
  assert.equal(start.run[1].params.url, '{{input.event[1]}}')
  assert.equal(start.daemon, true)
})
