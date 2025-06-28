window.onload = function() {
  liff.init({ liffId: "YOUR_LIFF_ID" })
    .then(() => {
      return liff.getProfile();
    })
    .then(profile => {
      console.log("LINEユーザー名", profile.displayName);
    });
};
