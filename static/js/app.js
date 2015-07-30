angular.module('klssignin', ['ngRoute'])
.config(function($routeProvider) {
  $routeProvider
  .when('/', {
    templateUrl:'templates/signin.html',
    controller: 'SigninCtrl'
  })
  .when('/register', {
      templateUrl:'templates/register.html',
      controller: 'RegisterCtrl'
  })
  ;
})
.controller('MainCtrl', function($scope) {

})
.controller('SigninCtrl', function($scope, $http, $location) {
  $scope.errorMessage = undefined;
  $scope.success = false;

  $scope.login = function(user) {
    $http.get('/signinout', {
      "params": {"username" : user.name}
    })
    .success(function(data,status) {
      if (data['is-child']) {
        $scope.student = {
          username: data['username'],
          inClass: data['in-class']
        };
      }
      $scope.success = true;
    }).error(function(data,status) {
      // 500 errors aren't our problem.
      if (status == 500) return;
      // if it's a 400 error, display the message to the client.
      if (status == 400) {
        $scope.errorMessage = data.message;
      }
    })
  }
})
.controller('RegisterCtrl', function($scope, $http, $location) {
    $scope.parents = [];
    $http.get("/parents").success(function(data) {
        $scope.parents = _.pairs(data);
    });

    $scope.delete_parent = function(parent) {
        console.log("Deleting " + parent);
        $http.delete("/parents", {params: {username: parent}});
    };

    $scope.update_parent = function(parent) {
        console.log("Updating " + parent);
        // TODO (phillip) Should only update the given params
        $http.put("/parents", {"username": parent, "params": {"children": ["Hank"]}});
    };

    $scope.create_parent = function() {
        var parent = "John";
        console.log("Creating " + parent);
        $http.post("/parents", {"username": parent});
    };

    $scope.delete_child = function(child) {
        console.log("Deleting " + child);
        $http.delete("/children", {params: {"username": child}});
    };

    $scope.update_child = function(child) {
        console.log("Updating " + child);
        // TODO (phillip) Should only update the given params
        $http.put("/children", {"username": child, "params": {"can_signout": true}});
    };

    $scope.create_child = function(child) {
        console.log("Creating " + child);
        $http.post("/children", {"username": child});
    };
})
;
