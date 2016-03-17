angular.module('starter.controllers', ['ngCordova','ui.router'])

.controller('DashCtrl', function($rootScope, $scope, $state, $ionicHistory, $translate, $http, $ionicLoading) {
  var RestServer = PersistData.get('RestServer');
  $http.get(RestServer + "/colors").then(function(response) {
    $scope.bgcolor = response.data.Colors[0].bgcolor;
    $scope.headercolor = response.data.Colors[0].header_color;
    $scope.fontcolor = response.data.Colors[0].font_color;
  });
  $rootScope.$on('$stateChangeStart', function (event, toState, toParams, fromState, fromParams) {
    $translate.use(PersistData.get('Preflanguage'));
    var salt = randomString(8);
    var RestServer = PersistData.get('RestServer');
    var UUID = PersistData.get('UUID');
    var DevSecret = PersistData.get('DevSecret');
    var localhash = md5(UUID + ':' + DevSecret + ':' + salt);
    var lang = PersistData.get('Preflanguage').substring(0,2).toLowerCase();
    if (['en','pt'].indexOf(lang) < 0) {
      lang = 'en';
    }
    $http.get(RestServer + "/verify?uuid=" + UUID + '&salt=' + salt).then(function(response) {
      if (response.data.Result !== localhash) {
        $ionicLoading.show({
          template: "<p>" + translations[lang]['NO_SERVER'] + "</p>",
          duration: 4000
        });
        $ionicHistory.currentView($ionicHistory.backView());
        $state.go('tab.setup',{}, {location: 'replace'});
      }
    }, function(err) {
      if (toState.name !== "tab.setup" && toState.name !== "tab.about") {
        $ionicLoading.show({
          template: "<p>" + translations[lang]['NO_SERVER'] + "</p>",
          duration: 4000
        });
        $ionicHistory.currentView($ionicHistory.backView());
        $state.go('tab.setup',{location: 'replace'});
      }
    })
  })
  $scope.restserver = PersistData.get('RestServer');
  $translate.use(PersistData.get('Preflanguage'));
})

.controller('LanguagesCtrl', function($scope, $ionicLoading, alllanguages) {
  $scope.restserver = PersistData.get('RestServer');
  $ionicLoading.show();
  $scope.languages = alllanguages;
  $ionicLoading.hide();
})

.controller('LangConfirmationCtrl', function($scope, $ionicLoading, $stateParams, Languages) {
  $scope.restserver = PersistData.get('RestServer');
  $scope.language = Languages.get($stateParams.langCode);
})

.controller('ScanResultCtrl', function($scope, $stateParams, getbarcode, $sce) {
  $scope.barcode = getbarcode;
  $scope.trustSrc = function(url) {
    return $sce.trustAsResourceUrl(url);
  };
  var RestServer = PersistData.get('RestServer');
  var Preflanguage = PersistData.get('Preflanguage');
  $scope.restserver = RestServer;
  var Votes = PersistData.get('Votes');
  if (Votes.split(':').indexOf($scope.barcode[0].id) < 0) {
    $scope.iconheart = 'ion-ios-heart-outline';
  } else {
    $scope.iconheart = 'ion-ios-heart';
  }
  $scope.media = {
    audio: RestServer + '/audios/' + Preflanguage + '-' + $scope.barcode[0].id + '.mp3',
    video: RestServer + '/videos/' + Preflanguage + '-' + $scope.barcode[0].id + '.ogv'
  };
})

.controller('BarcodeScan', function($scope, $state, $ionicPlatform, $cordovaBarcodeScanner, $ionicLoading) {
  $scope.code = '';
  $scope.searchcode = function() {
    if ($scope.code.length > 2) {
      $state.go('tab.scanresult',{scanID: this.code, type: 'search'});
    };
  };
  $scope.scanBarcode = function() {
    $ionicPlatform.ready(function() {
      $cordovaBarcodeScanner.scan().then(function(imageData) {
        var ID = imageData.text;
        if (imageData.format === 'QR_CODE' && ID.trim().length > 0) {
          $state.go('tab.scanresult', {scanID: ID.trim(), type: 'qrcode'}, {location: 'replace'});
        } else {
          $ionicLoading.show({
            template: "<p>Error</p>",
            duration: 3000
          });
        }
      }, function(error) {
        $ionicLoading.show({
          template: "<p>Error</p>",
          duration: 3000
        });
      });
    });
  };
})

.controller('ChangeLanguageCtrl', function($translate, $scope) {
  $scope.changeLanguage = function(langKey) {
    PersistData.set('Preflanguage', langKey);
    $translate.use(langKey);
  };
})

.controller('VoteCtrl', function($scope, $http, $q) {
  var RestServer = PersistData.get('RestServer');
  $scope.vote = function(objID) {
    var Votes = PersistData.get('Votes');
    var Votes_arr = Votes.split(':');
    if ( Votes_arr.indexOf(objID) < 0) {
      $http.get(RestServer + "/vote?type=plus&id=" + objID).then(function(response) {
        if (response.data.result == 'ok') {
          $scope.result.votes++;
          $scope.iconheart = 'ion-ios-heart';
          PersistData.set('Votes', Votes + ':' + objID);
        }
      });
    } else {
      $http.get(RestServer + "/vote?type=minus&id=" + objID).then(function(response) {
        if (response.data.result == 'ok') {
          $scope.result.votes--;
          $scope.iconheart = 'ion-ios-heart-outline';
          PersistData.set('Votes', Votes_arr.splice(Votes_arr.indexOf(objID)-1,1).join(':'));
        }
      });
    }
  };
})

.controller('SuggestionsCtrl', function($state, $scope, getsuggestions) {
  $scope.suggestions = getsuggestions;
  var RestServer = PersistData.get('RestServer');
  $scope.restserver = RestServer;
  $scope.doRefresh = function() {
    $scope.$broadcast('scroll.refreshComplete');
    $state.go($state.current, {}, {reload: true});
  }
})

.controller('HistoryCtrl', function($state, $scope, gethistory) {
  var RestServer = PersistData.get('RestServer');
  $scope.restserver = RestServer;
  $scope.userhistory = gethistory;
  $scope.doRefresh = function() {
    $scope.$broadcast('scroll.refreshComplete');
    $state.go($state.current, {}, {reload: true});
  }
})

.controller('SetupCtrl', function($state, $scope, $rootScope, $ionicHistory, $translate, $ionicPopup, $ionicPlatform, $ionicLoading, $cordovaBarcodeScanner, $http) {
  $ionicHistory.currentView($ionicHistory.backView());
  var RestServer = PersistData.get('RestServer');
  var DevSecret = PersistData.get('DevSecret');
  var Preflanguage = PersistData.get('Preflanguage').substring(0,2).toLowerCase();
  if (['en','pt'].indexOf(Preflanguage) > 0) {
    $scope.translations = translations[Preflanguage];
  } else {
    $scope.translations = translations['en'];
  }
  /*
  Until now, we don't trust in any server. It's not safe to show images,
  audios or texts from a remote server. We need to take care what show to the user!

  How this process works:
  1) Read a RSA Public key and the Server IP address from a QR Code
    1.1) The theory of asymmetric cryptography says: "Only the private owner
         can read a message encrypted with the public key".
  2) We will generate a random password and encrypt it with the public key
  3) We will send to server our UUID (an unique identification),
     our encrypted password and a salt (salt is a random password used to generate an hash)
     3.1) Only the server will be able to decode our encrypted password
  4) The server will decode the password and generate a MD5 hash with
     our uuid, the password and the salt.
  5) We will do the a MD5 hash with same informations and compares it.
    5.1) If the hash matches, we have a trustee server.
    5.2) If not, someone is trying to fake the real server! (and possibly sent fake texts and photos!)
  6) After a trustee is made, before show something to the user, we will send
     a verify message to server. If the hash matches we show the response, if not
     a message "no trusted server is available" is presented to user.
  Why use a salt?
  Well, if we don't use it the hash will be always the same! It's vary easy to replay this!
  With a random salt we have a true OTP (One Time Password) algorithm.
  This will make things dificult to an attacker.

  */

  // Let's verify the last server used if it's valid or not.
  $scope.reuse = function() {
    var hashserver = null;
    var UUID = PersistData.get('UUID');
    var Salt = randomString(8);
    // We will generate an hash with our deviceuuid, our password and a random salt.
    var localhash = md5(UUID + ':' + DevSecret + ':' + Salt);
    // Send our uuid and the salt to the server with a "verify" request.
    $http.get(RestServer + "/verify?uuid=" + UUID + '&salt=' + Salt).then(function(response) {
      hashserver = response.data.Result;
      // Receive an hash as response
      // Only the owner of priv key is able to generate the correct hash.
    }).finally(function() {
      if (localhash === hashserver) {
        // Yes! It's our trustee server!
        // Now it's safe to show it's images and text to the user!
        $translate.use(PersistData.get('Preflanguage'));
        $ionicLoading.show({
          template: "{{'MAIN.SERVER_DETECTED' | translate}}",
          duration: 3000
        });
        $translate.use(PersistData.get('Preflanguage'));
        $rootScope.hideTabs = '';
        $ionicHistory.currentView($ionicHistory.backView());
        $state.go('tab.dash',{}, {location: 'replace'});
      }
    })
  }
  // Do last server verification.
  $scope.reuse();

  $scope.setup = function() {
    // Let's setup a trusted server!
    $ionicPlatform.ready(function() {
      var UUID = PersistData.get('UUID');
      // First, read the QR Code with server IP and Public Key
      $cordovaBarcodeScanner.scan().then(function(imageData) {
        // Split the text into an Array.
        // [0] is the Server IP
        // [1] is the Public Key
        if (imageData.format === "QR_CODE" && imageData.text.length > 0) {
          var dataArray = imageData.text.split('|');
          if (dataArray.length === 2) {
            RestServer = dataArray[0].trim();
            if (RestServer.substring(0, 4) !== "http") {
              RestServer = "http://" + dataArray[0].trim();
            }
            var PublicKey = dataArray[1].trim();
          } else if ( dataArray.length === 1 ){
            var PublicKey = dataArray[0].trim();
            RestServer = 'http://192.168.20.101:5000';
          } else {
            var PublicKey = null;
            RestServer = null;
          }
          // The Public Key is present?
          if (PublicKey !== null) {
            // If yes, let's do the handshake!
            // First generate a random password with 32 characteres
            var DevSecret = randomString(32);
            // Then, encrypt with the public key.
            var crypt = new JSEncrypt();
            crypt.setKey(PublicKey);
            // Only the woner of the correct private key will decrypt our password
            var EncSecret = crypt.encrypt(DevSecret);
            var attempt = 1;
            while ((EncSecret === false) && (attempt < 5)) {
              crypt.setKey(PublicKey);
              EncSecret = crypt.encrypt(DevSecret);
              attempt++;
            }
            // Generate a Salt for our handshake. 8 characteres is enougth.
            var Salt = randomString(8);
            // Generate a hash with our DeviceID, our secret and the salt
            var localhash = md5(UUID + ':' + DevSecret + ':' + Salt);
            // Send our encrypted password, our deviceuid and the salt
            // Only the owner of the correct private key will be able to generate
            // the correct hash with deviceuid, the password and the salt!
            $http.get(RestServer + "/setup?uuid=" + UUID + '&salt=' + Salt + '&code=' + EncSecret).then(function(response) {
              if (response.data.Result === localhash) {
                // Everything OK. Server return a valid hash! It's our trustee server!
                // Now, save the password and server IP address into device.
                PersistData.set('DevSecret', DevSecret);
                PersistData.set('RestServer', RestServer);
                // Now, we need to reboot the application.
                // This is needed by the translate function.
                // Unfortunately, translateProvider only can be used into ".config" function...
                $ionicPopup.show({
                  title: '<h3>Virtual Guide</h3>',
                  subTitle: '<h4>' + translations[Preflanguage]['POPUP_TITLE'] + '</h4>',
                  template: translations[Preflanguage]['POPUP_BODY'],
                  scope: $scope,
                    buttons: [{
                        text: '<b>OK</b>',
                        type: 'button-positive button-block',
                        onTap: function(e) {
                          if (ionic.Platform.isAndroid()) {
                            navigator.app.loadUrl("file:///android_asset/www/index.html");
                          } else {
                            navigator.app.loadUrl("file:///ios_asset/www/index.html");
                            ionic.Platform.exitApp();
                          }
                        }
                      }]
                });
              } else {
                $ionicLoading.show({
                  template: '<p>' + translations[Preflanguage]['POPUP_TITLE'] + '</p>',
                  duration: 4000
                });
              }
            }), function(e) {
              $ionicLoading.show({
                template: '<p>' + translations[Preflanguage]['POPUP_TITLE'] + '</p>',
                duration: 4000
              });
            }
          }
        } else {
          $ionicLoading.show({
            template: '<p>Error</p>',
            duration: 4000
          });
        }
      })
    })
  }
})

.controller('RegisterModalCtrl', function($scope, $ionicModal) {
  $ionicModal.fromTemplateUrl('templates/modal-register.html', {
    scope: $scope,
    animation: 'slide-in-up'
  }).then(function(modal) {
    $scope.modal = modal
  })
  $scope.openModal = function() {
    $scope.modal.show();
  }
  $scope.closeModal = function() {
    $scope.modal.hide();
  }
  $scope.$on('$destroy', function() {
    $scope.modal.remove();
  });
})

.controller('ExitCtrl', function($scope, $ionicHistory) {
  $scope.ExitApp = function() {
    ionic.Platform.exitApp();
    navigator.app.exitApp();
  }
  $scope.RestartApp = function() {
    if (ionic.Platform.isAndroid()) {
      navigator.app.loadUrl("file:///android_asset/www/index.html");
    }
  }
})

.controller('ButtonsCtrl', function($state, $scope, $ionicHistory, $ionicSideMenuDelegate, $location) {
  $scope.gobackone = function() {
    if ($ionicHistory.backTitle() === null ) {
      $state.go('tab.dash');
    } else {
      $ionicHistory.goBack(-1);
    }
  }
  $scope.hidebutton = function() {
    if ($location.path() === "/tab/setup" || $location.path() === "/tab/about_app") {
      $ionicSideMenuDelegate.canDragContent(false);
      return true;
    } else {
      $ionicSideMenuDelegate.canDragContent(true);
      return false;
    }
  }
})

.directive('hideTabs', function($rootScope) {
  return {
      restrict: 'A',
      link: function($scope, $el) {
          $rootScope.hideTabs = 'tabs-item-hide';
          $scope.$on('$destroy', function() {
              $rootScope.hideTabs = '';
          });
      }
  };
});
