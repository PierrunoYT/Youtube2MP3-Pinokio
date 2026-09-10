module.exports = {
  run: [
    {
      method: "fs.rm",
      params: {
        path: "app/env"
      }
    },
    {
      method: "notify",
      params: {
        html: "Reset complete! The environment has been removed. Click 'Install' to reinstall."
      }
    }
  ]
}
