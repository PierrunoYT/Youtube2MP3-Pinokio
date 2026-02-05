module.exports = {
  daemon: true,
  env: [],
  run: [
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: [
          "python app.py"
        ],
        on: [{
          // Monitor for Gradio local URL output (localhost)
          "event": "/http:\\/\\/127\\.0\\.0\\.1:\\d{2,5}/",
          "done": true
        }]
      }
    },
    // Set the local URL variable for the "Open Web UI" button
    {
      method: "local.set",
      params: {
        url: "{{input.event[0]}}"
      }
    },
    {
      method: "notify",
      params: {
        html: "YouTube2DL is running! Click 'Open Web UI' to open the downloader."
      }
    }
  ]
}
