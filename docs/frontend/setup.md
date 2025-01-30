# Frontend setup

I reinstalled nodejs and pnpm to get a fresh start. Make sure these are installed. 

## Created react app
```
pnpm create react-app frontend
```

make sure the peer dependencies are set to legacy with 

```
npm config set legacy-peer-deps true
```
# Dependencies

I will use the following dependencies to create a robust frontend:
- react router
- react redux
- material UI
- chakra UI
- shadcn UI from tailwindcss

# We set up tailwind css with installing:
- tailwind css
- postcss
- autoprefixer

src/index contains the tailwindcss directives now. a tailwind.config.js was created to export all files that will build th efront end. THe config.js file had to be created manually because when doing the init it gave a missing binaries error.

# We set up redux
- created redux store in src/store.js
- wrapped the app in the redux provider in src/index.js

# We set up react router
src/App.js was just replaced with a simple page using router that includes an about page and home page. Home.js and About.js were created with basic sample text in them. 

# run it
run the app with pnpm start

go to port 3000 to view the react app. 

# what's next

further development will be to create different elements like buttons and such. We will combine our learning experience with creating some elements myself and using open source elements and widgets. 