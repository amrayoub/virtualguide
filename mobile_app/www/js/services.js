var App = angular.module('starter.services', ['ionic','ngCordova'])

App.factory('Languages', function($http, $q, $state, $ionicLoading) {
  var languages = [];
  var RestServer = PersistData.get('RestServer');
  return {
    all: function() {
      var dfd = $q.defer();
      $http.get(RestServer + "/languages").then(function(response) {
        languages = response.data.Languages;
        dfd.resolve(languages);
      }, function(err) {
        $ionicLoading.show({
          template: 'No valid server connection',
          duration: 5000
        });
      });
      return dfd.promise;
    },
    get: function(langCode) {
      for (var i = 0; i < languages.length; i++) {
        var isocode = languages[i].code + '-' + languages[i].locale;
        if (isocode == langCode) {
          return languages[i];
        }
      }
      return null;
    }
  }
})

App.factory('ScanResult', function($state, $http, $q, $ionicLoading) {
  var result = [];
  var RestServer = PersistData.get('RestServer');
  var UUID = PersistData.get('UUID');
  return {
    get: function(scanID, type) {
      var Preflanguage = PersistData.get('Preflanguage');
      if (type == 'qrcode') {
        var dfd = $q.defer();
        $http.get(RestServer + "/object?id=" + scanID + '&lang=' + Preflanguage + '&uuid=' + UUID).then(function(response) {
          result = response.data.Object;
          dfd.resolve(result);
        }, function(err) {
          $ionicLoading.show({
            template: "<p>{{'SCAN_TAB.UNKNOW_CODE' | translate}}</p><p>{{'SCAN_TAB.TRY_AGAIN' | translate}}</p>",
            duration: 2500
          });
        });
        return dfd.promise;
      } else if (type == 'search') {
        var dfd = $q.defer();
        $http.get(RestServer + "/object?type=search&id=" + scanID + '&lang=' + Preflanguage + '&uuid=' + UUID).then(function(response) {
          result = response.data.Object;
          if (result.length < 1) {
            $state.go('tab.scan');
            $ionicLoading.show({
              template: "<p>{{'SCAN_TAB.UNKNOW_CODE' | translate}}</p><p>{{'SCAN_TAB.TRY_AGAIN' | translate}}</p>",
              duration: 2500
            });
          }
          dfd.resolve(result);
        }, function(err) {
          $ionicLoading.show({
            template: "<p>{{'SCAN_TAB.UNKNOW_CODE' | translate}}</p><p>{{'SCAN_TAB.TRY_AGAIN' | translate}}</p>",
            duration: 2500
          });
        });
        return dfd.promise;
      }
    },
  }
})

App.factory('Suggestions', function($state, $http, $q) {
  var result = [];
  var RestServer = PersistData.get('RestServer');
  return {
    get: function() {
      var Preflanguage = PersistData.get('Preflanguage');
      var dfd = $q.defer();
      $http.get(RestServer + "/suggestions" + '?lang=' + Preflanguage).then(function(response) {
        result = response.data.Suggestions;
        dfd.resolve(result);
      }, function(err) {
        null;
      });
      return dfd.promise;
    }
  }
})

App.factory('UserHistory', function($state, $http, $q) {
  var result = [];
  var RestServer = PersistData.get('RestServer');
  var UUID = PersistData.get('UUID');
  return {
    get: function() {
      var dfd = $q.defer();
      $http.get(RestServer + "/history" + '?uuid=' + UUID).then(function(response) {
        result = response.data.History;
        dfd.resolve(result);
      }, function(err) {
        null;
      });
      return dfd.promise;
    }
  }
});
