function updateContent(langData) {
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        element.textContent = langData[key];
    });
  }
    // Function to fetch language data
  async function fetchLanguageData(lang) {
      // console.log(`{{ url_for('static', filename='assets/languages/${lang}.json') }}`);
      // const filename = ``;
      
      var url = `http://127.0.0.1:5000/static/assets/languages/en.json`;
      if (lang == 'cn'){
        url = `http://127.0.0.1:5000/static/assets/languages/cn.json`;
      }
      const response = await fetch(url);
      return response.json();
  }

  // Function to set the language preference
  function setLanguagePreference(lang) {
      localStorage.setItem('language', lang);
      // location.reload();
  }

    async function changeLanguage(lang) {
        await setLanguagePreference(lang);
        console.log(lang);
        const langData = await fetchLanguageData(lang);
        updateContent(langData);
    }
