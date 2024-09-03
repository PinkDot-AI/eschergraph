// @ts-check
// `@type` JSDoc annotations allow editor autocompletion and type checking
// (when paired with `@ts-check`).
// There are various equivalent ways to declare your Docusaurus config.
// See: https://docusaurus.io/docs/api/docusaurus-config

import {themes as prismThemes} from 'prism-react-renderer';

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'EscherGraph | PinkDot AI',
  tagline: 'The EscherGraph!',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://eschergraph.docs.pinkdot.ai',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'PinkDot AI', // Usually your GitHub org/user name.
  projectName: 'EscherGraph', // Usually your repo name.

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
        },
        blog: {
          showReadingTime: true,
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
      image: 'img/pinkdot.png',
      navbar: {
        title: 'EscherGraph',
        logo: {
          alt: 'PinkDot AI logo',
          src: './img/pinkdot.png',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: 'Tutorial',
          },
          {href:'https://pinkdot.ai/blogs', label: 'Blog', position: 'left'},
          {
            href: 'https://github.com/pinkdotai/eschergraph',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {
                label: 'Getting started',
                to: '/docs/getting_started',
              },
              {
                label: 'EscherGraph Explained',
                to: '/docs/category/explained-eschergraph',
              },
              {
                label: 'Comming soon | Contributions',
                to: '/docs/coming_soon',
              },
              {
                label: 'PinkDot AI Home',
                href: 'https://pinkdot.ai',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              // {
              //   label: 'Stack Overflow',
              //   href: 'https://stackoverflow.com/questions/tagged/docusaurus',
              // },
              {
                label: 'Discord',
                href: 'https://discord.gg/P5gzsNVb',
              },
              // {
              //   label: 'Twitter',
              //   href: 'https://twitter.com/docusaurus',
              // },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'Blog',
                href:'https://pinkdot.ai/blogs',
              },
              {
                label: 'GitHub',
                href: 'https://github.com/pinkdotai/eschergraph',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} EscherGraph | PinkDot AI B.V.`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
      },
    }),
};

export default config;
