'use strict'

const path = require('node:path')
const ghPages = require('gh-pages')
const Git = require('gh-pages/lib/git.js')

// gh-pages normally expands every deployed file into a single `git rm`
// invocation. The forecast viewer contains hundreds of frames, which exceeds
// Windows' command-line length limit. Removing the deployment root is
// equivalent here and keeps the Git command short.
Git.prototype.rm = function removePublishedTree() {
  return this.exec('rm', '--ignore-unmatch', '-r', '-f', '--', '.')
}

const dist = path.resolve(__dirname, '..', 'dist')

const publish = new Promise((resolve, reject) => {
  ghPages.publish(dist, { dotfiles: true, nojekyll: true }, (error) => {
    if (error) reject(error)
    else resolve()
  })
})

publish
  .then(() => process.stdout.write('Published\n'))
  .catch((error) => {
    process.stderr.write(`${error.stack || error}\n`)
    process.exitCode = 1
  })
