// Ionic Starter App

// angular.module is a global place for creating, registering and retrieving Angular modules
// 'starter' is the name of this angular module example (also set in a <body> attribute in index.html)
// the 2nd parameter is an array of 'requires'
// 'starter.services' is found in services.js
// 'starter.controllers' is found in controllers.js
var App = angular.module('starter', ['ionic', 'starter.controllers', 'starter.services','pascalprecht.translate'])

var randomString = function(length) {
    var text = "";
    var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    for(var i = 0; i < length; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}

var PersistData = new Persist.Store('VirtualGuide');

var translations = {
  'pt': {
    'NO_SERVER': 'Não existe servidor disponível.',
    'NOUUID': 'Não foi possível determinar o UUID do dispositivo.\nTente abrir o aplicativo novamente.',
    'SETUP_TITLE': 'Configurar Confiança',
    'SCAN_BUTTON': 'Capturar Código de Segurança',
    'EXIT_BUTTON': 'Sair do aplicativo',
    'NO_TRUSTED': 'Não existem servidores disponíveis.',
    'SCAN_TEXT': 'Antes de utilizar o Virtual Guide pela primeira vez,\
     é necessário estabelecer a confiança com um provedor de conteúdo.\
     Para estabelecer a confiança, é necessário capturar um QR Code disponibilizado\
     pelo provedor do conteúdo.',
     'POPUP_TITLE': 'Sucesso.',
     'POPUP_BODY': 'O processo ocorreu sem problemas!\n\
     Por razoẽs de segurança, é necessário fechar e abrir o Aplicativo Virtual Guide novamente.'
  },
  'en': {
    'NO_SERVER': 'No server available.',
    'NOUUID': 'Device UUID can not be determined. Please, reopen application.',
    'SETUP_TITLE': 'Setup Trustee',
    'SCAN_BUTTON': 'Scan Security Code',
    'EXIT_BUTTON': 'Exit application',
    'NO_TRUSTED': 'No servers available.',
    'SCAN_TEXT': 'Scan Configuration QR Code',
    'POPUP_TITLE': 'Success.',
    'POPUP_BODY': 'The proccess works perfectly!\n\
    For security reasons, it\'s necessary exit Virtual Guide Application and reopen it.'
  }
};

App.run(function($ionicPlatform, $translate, $ionicHistory, $ionicPopup, $cordovaDevice) {
  var Preflanguage = 'unknow';
  $ionicPlatform.ready(function() {

    $ionicPlatform.registerBackButtonAction(function(e) {
      e.preventDefault();
      function showConfirm() {
        var confirmPopup = $ionicPopup.confirm({
          title: '<strong>Exit?</strong>',
          template: 'Are you sure you want to exit?'
        });
        confirmPopup.then(function(res) {
          if (res) {
            ionic.Platform.exitApp();
          } else {
          }
        });
      }
      if ($rootScope.$viewHistory.backView) {
        $rootScope.$viewHistory.backView.go();
      } else {
        showConfirm();
      }
      return false;
    }, 101);

    i = 0;
    var UUID = $cordovaDevice.getUUID();
    while (UUID === null && i < 5) {
      UUID = $cordovaDevice.getUUID();
      i++
    }
    if (UUID === null) {
      alert(translations[Preflanguage]['NOUUID']);
      ionic.Platform.exitApp();
    }
    PersistData.set('UUID', UUID);

    if (typeof navigator.globalization !== "undefined") {
      navigator.globalization.getPreferredLanguage(function(language) {
        Preflanguage = language.value;
      }, null);
    }
    if (window.cordova && window.cordova.plugins && window.cordova.plugins.Keyboard) {
      cordova.plugins.Keyboard.hideKeyboardAccessoryBar(true);
      cordova.plugins.Keyboard.disableScroll(true);
    }
    if (window.StatusBar) {
      StatusBar.styleDefault();
    }
  })
  if (Preflanguage == 'unknow') {
    Preflanguage = window.navigator.language.toLowerCase();
  }

  PersistData.set('Preflanguage', Preflanguage);
  $translate.use(Preflanguage);
})

App.config(function($stateProvider, $httpProvider, $urlRouterProvider, $translateProvider) {
  $httpProvider.defaults.withCredentials = true;
  PersistData.set('Votes', ':');
  var RestServer = PersistData.get('RestServer');
  if (RestServer !== null) {
    $translateProvider.useUrlLoader(RestServer + '/translation');
  }
  $translateProvider.useSanitizeValueStrategy('sanitizeParameters');
  $translateProvider.forceAsyncReload(true);
})

App.config(function($stateProvider, $urlRouterProvider) {
  $stateProvider

  .state('tab', {
    url: '/tab',
    abstract: true,
    templateUrl: 'templates/tabs.html'
  })

  .state('tab.setup', {
    url: '/setup',
    views: {
      'tab-setup': {
        templateUrl: 'templates/tab-setup.html',
        controller: 'SetupCtrl'
      }
    }
  })

.state('tab.dash', {
  url: '/dash',
  views: {
    'tab-dash': {
      templateUrl: 'templates/tab-dash.html',
      controller: 'DashCtrl'
    }
  }
})

.state('tab.languages', {
  url: '/languages',
  views: {
    'tab-languages': {
      templateUrl: 'templates/tab-languages.html',
      controller: 'LanguagesCtrl',
      resolve: {
        alllanguages: function(Languages) {
          return Languages.all();
        }
      }
    }
  }
})

.state('tab.langconfirmation', {
  url: '/langs/{langCode}',
  views: {
    'tab-languages': {
      templateUrl: 'templates/lang-confirmation.html',
      controller: 'LangConfirmationCtrl'
    }
  }
})

.state('tab.scan', {
  url: '/scan',
  views: {
    'tab-scan': {
      templateUrl: 'templates/tab-scan.html',
      controller: 'BarcodeScan'
    }
  }
})

.state('tab.scanresult', {
  url: '/scans/{scanID}?{type}',
  views: {
    'tab-scan': {
      templateUrl: 'templates/scan-result.html',
      controller: 'ScanResultCtrl',
      resolve: {
        getbarcode: function($stateParams, ScanResult) {
          return ScanResult.get($stateParams.scanID, $stateParams.type);
        }
      }
    }
  }
})

.state('tab.suggestions', {
  url: '/suggestions',
  views: {
    'tab-suggestions': {
      templateUrl: 'templates/tab-suggestions.html',
      controller: 'SuggestionsCtrl',
      resolve: {
        getsuggestions: function(Suggestions) { return Suggestions.get(); }
      }
    }
  }
})

.state('tab.userhistory', {
  url: '/userhistory',
  views: {
    'tab-userhistory': {
      templateUrl: 'templates/tab-history.html',
      controller: 'HistoryCtrl',
      resolve: {
        gethistory: function(UserHistory) { return UserHistory.get(); }
      }
    }
  }
})

.state('tab.about', {
  url: '/about',
  views: {
    'tab-about': {
      templateUrl: 'templates/tab-about.html'
    }
  }
})

.state('tab.about_app', {
  url: '/about_app',
  views: {
    'tab-about-app': {
      templateUrl: 'templates/tab-about-app.html'
    }
  }
});

$urlRouterProvider.otherwise('/tab/setup');
});
