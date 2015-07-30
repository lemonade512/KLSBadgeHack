angular.module('klssignin', ['ngRoute'])
.config(function($routeProvider) {
  $routeProvider
  .when('/', {
    templateUrl:'templates/signin.html',
    controller: 'SigninCtrl'
  })
  ;
})
.controller('MainCtrl', function($scope) {

})
.controller('SigninCtrl', function($scope, $http, $location) {
  $scope.login = function(user) {
    $http.get('/')
  }
})
;
