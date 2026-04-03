module.exports = {
  daemon: true,
  run: [
    {
      method: "shell.run",
      params: {
        venv: "env",
        env: {},
        path: "app",
        message: [
          "python app.py"
        ],
        on: [{
          // Capture group 1 = full http URL (Gradio / local servers); input.event[1] per Pinokio + Gepeto skill
          "event": "/(http:\/\/\\S+)/",
          "done": true
        }]
      }
    },
    {
      method: "local.set",
      params: {
        url: "{{input.event[1]}}"
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
