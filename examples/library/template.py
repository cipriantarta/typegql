# flake8: noqa
TEMPLATE = '''
<!DOCTYPE html>
<html>
  <head>
    <meta charset=utf-8 />
    <meta name="viewport" content="user-scalable=no, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, minimal-ui">
    <link rel="shortcut icon" href="https://graphcool-playground.netlify.com/favicon.png">
    <title>JEANS Playground</title>
    <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/graphql-playground-react@1.7.20/build/static/css/index.css" />
    <link rel="shortcut icon" href="//cdn.jsdelivr.net/npm/graphql-playground-react@1.7.20/build/favicon.png" />
    <script src="//cdn.jsdelivr.net/npm/graphql-playground-react@1.7.20/build/static/js/middleware.js"></script>
  </head>
  <body>
    <div id="loading-wrapper">
      <svg class="logo" viewBox="0 0 128 128" xmlns:xlink="http://www.w3.org/1999/xlink">
        <title>GraphQL Playground Logo</title>
        <defs>
          <linearGradient id="linearGradient-1" x1="4.86%" x2="96.21%" y1="0%" y2="99.66%">
            <stop stop-color="#E00082" stop-opacity=".8" offset="0%"></stop>
            <stop stop-color="#E00082" offset="100%"></stop>
          </linearGradient>
        </defs>
        <g>
          <rect id="Gradient" width="127.96" height="127.96" y="1" fill="url(#linearGradient-1)" rx="4"></rect>
          <path id="Border" fill="#E00082" fill-rule="nonzero" d="M4.7 2.84c-1.58 0-2.86 1.28-2.86 2.85v116.57c0 1.57 1.28 2.84 2.85 2.84h116.57c1.57 0 2.84-1.26 2.84-2.83V5.67c0-1.55-1.26-2.83-2.83-2.83H4.67zM4.7 0h116.58c3.14 0 5.68 2.55 5.68 5.7v116.58c0 3.14-2.54 5.68-5.68 5.68H4.68c-3.13 0-5.68-2.54-5.68-5.68V5.68C-1 2.56 1.55 0 4.7 0z"></path>
          <path class="bglIGM" x="64" y="28" fill="#fff" d="M64 36c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8" style="transform: translate(100px, 100px);"></path>
          <path class="ksxRII" x="95.98500061035156" y="46.510000228881836" fill="#fff" d="M89.04 50.52c-2.2-3.84-.9-8.73 2.94-10.96 3.83-2.2 8.72-.9 10.95 2.94 2.2 3.84.9 8.73-2.94 10.96-3.85 2.2-8.76.9-10.97-2.94"
            style="transform: translate(100px, 100px);"></path>
          <path class="cWrBmb" x="95.97162628173828" y="83.490001.7.20668" fill="#fff" d="M102.9 87.5c-2.2 3.84-7.1 5.15-10.94 2.94-3.84-2.2-5.14-7.12-2.94-10.96 2.2-3.84 7.12-5.15 10.95-2.94 3.86 2.23 5.16 7.12 2.94 10.96"
            style="transform: translate(100px, 100px);"></path>
          <path class="Wnusb" x="64" y="101.97999572753906" fill="#fff" d="M64 110c-4.43 0-8-3.6-8-8.02 0-4.44 3.57-8.02 8-8.02s8 3.58 8 8.02c0 4.4-3.57 8.02-8 8.02"
            style="transform: translate(100px, 100px);"></path>
          <path class="bfPqf" x="32.03982162475586" y="83.490001.7.20668" fill="#fff" d="M25.1 87.5c-2.2-3.84-.9-8.73 2.93-10.96 3.83-2.2 8.72-.9 10.95 2.94 2.2 3.84.9 8.73-2.94 10.96-3.85 2.2-8.74.9-10.95-2.94"
            style="transform: translate(100px, 100px);"></path>
          <path class="edRCTN" x="32.033552169799805" y="46.510000228881836" fill="#fff" d="M38.96 50.52c-2.2 3.84-7.12 5.15-10.95 2.94-3.82-2.2-5.12-7.12-2.92-10.96 2.2-3.84 7.12-5.15 10.95-2.94 3.83 2.23 5.14 7.12 2.94 10.96"
            style="transform: translate(100px, 100px);"></path>
          <path class="iEGVWn" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" d="M63.55 27.5l32.9 19-32.9-19z"></path>
          <path class="bsocdx" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" d="M96 46v38-38z"></path>
          <path class="jAZXmP" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" d="M96.45 84.5l-32.9 19 32.9-19z"></path>
          <path class="hSeArx" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" d="M64.45 103.5l-32.9-19 32.9 19z"></path>
          <path class="bVgqGk" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" d="M32 84V46v38z"></path>
          <path class="hEFqBt" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" d="M31.55 46.5l32.9-19-32.9 19z"></path>
          <path class="dzEKCM" id="Triangle-Bottom" stroke="#fff" stroke-width="4" d="M30 84h70" stroke-linecap="round"></path>
          <path class="DYnPx" id="Triangle-Left" stroke="#fff" stroke-width="4" d="M65 26L30 87" stroke-linecap="round"></path>
          <path class="hjPEAQ" id="Triangle-Right" stroke="#fff" stroke-width="4" d="M98 87L63 26" stroke-linecap="round"></path>
        </g>
      </svg>
      <div class="text">Loading
        <span class="dGfHfc">JEANS Playground</span>
      </div>
    </div>
    <div id="root" />
    <script type="text/javascript">
      window.addEventListener('load', function (event) {
          const urlParams = new URLSearchParams(window.location.search);
          const token = urlParams.get('access_token');
          const root = document.getElementById('root');
          root.classList.add('playgroundIn');
          GraphQLPlayground.init(root, {
              "endpoint": "/graphql",
              "subscriptionEndpoint": "/graphql",
              "version": "1.7.20",
              "canSaveConfig": true,
              "settings": {
                "schema.polling.enable": false
              }
          })
        })
    </script>
  </body>
</html>
'''
