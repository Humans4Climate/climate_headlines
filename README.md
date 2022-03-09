# Climate Headlines

Climate Headlines is your centralized location to get your daily news about anything related to climate change.

Climate change is the most pressing existential threat of our generation. There's a vast amount of information out there, but it's difficult to find and to extract a cohesive story out of it.

Climate Headlines aims to be the place you can go to in order to find the latest you need to know about climate change.

This submission includes the backend of Climate Headlines: an app that retrieves hundreds of news every day from trusted sources devoted to climate. You can find stories by the mainstream media outlets like The New York Times or The Guardian, but also smaller stories by local newspapers that tell the story of how climate change is affecting people today.

The app is an Azure Function. It uses an RSS reader and Bing Search to find all the relevant news, every day. Then it uniques and stores them in a non-relational database (MongoDB). We're still working on a website to surface the news (if you're a Front End or Webflow developer, and are interested in collaborating, send us an email!). For now, we're putting them in a Google Spreadsheet that you can access here. It gets updated every day. We also tweet the best piece on our Twitter account.

# Code summary

This repo contains the backend for Climate Headlines. As mentioned above, it's an Azure Function. It runs every day at 2pm PST (this might change in the future).

There are two ways of obtaining news: via RSS feeds and via the Bing search API. Some of the more established new sources provide RSS feeds (thank you!) that you can just query and get the most up to date stories. This has the benefit of knowing that the news found here will always be relevant. The Bing search API is more hit-or-miss - sometimes you get great finds that you wouldn't otherwise have ever read. But sometimes they're not that relevant. The search is keyword based, and it works well for the most part, but sometimes you'll get a result that's actually unrelated.

After all news are aggregated, they're stored in a MongoDB for the posterity. Once that's done, we're exposing them on a [Google spreadsheet](https://docs.google.com/spreadsheets/d/1Rvtaj33eCdO9O8pNkpKhgOv_FZd0frFE47tsKBeN2eM/edit#gid=1699870975) and sometimes [tweeting](https://twitter.com/ClimateHumans4) them automatically, too.

# Collaboration

As pointed out above, we don't have a front end for Climate Headlines yet. If you're interested in collaborating and you think you can help with that, please reach out! We're working on a Webflow app first but also open to a custom front end.

We have big plans for Climate Headlines - we want to do some NLP on the news to be able to see what the general public opinion is like, or how topics are changing over time. We're also open to any other additions to the oveerall idea of sharing information around climate and its urgency.

If any of this sounds interesting, drop us a line at [humans@climateheadlines.co](mailto:humans@climateheadlines.co). Thanks for caring!
