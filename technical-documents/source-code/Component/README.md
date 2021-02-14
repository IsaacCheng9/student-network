This component was created with [BuilderX](https://cloud.builderx.io/).

## BuilderX uses third party libraries for some of the react components such as

```
@material-ui/core@4.2.1
google-map-react@1.1.4
material-ui-slider@3.0.8
pure-react-carousel@1.21.1
react-list@0.8.11
react-router-dom@5.0.1
styled-components@4.3.2
react-native-vector-icons
```

You can add these packages by running `yarn add [packageName]` or `npm install [packageName]`

## Please add the extracted component folder in your project and import the component folder.

Eg import Component from `[folder path]`

**Note: You might need to load custom fonts that has been used in the component. Font files are available in the `assets/fonts` folder.**

- Create style.css at the root of you project
- Add each font like this

```
@font-face {
  font-family: <fontName>;
  src: url(<relative-path-to-font-file>) format(<file-format>);
}
```

- import style.css in your index.js file
