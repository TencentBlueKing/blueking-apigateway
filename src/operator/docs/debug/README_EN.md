## debug cli tool
Provide resource query and environment release version query functions for configuring data for the control plane and gateway configuration data for the data plane
## Features

```shell
micro-gateway-operator --help
```
output：
```shell
bk-gateway operator for apisix                                                                                                                                                                          
                                                                                                                                                                                                        
Usage:                                                                                                                                                                                                  
  bk-apigateway-operator [flags]                                                                                                                                                                        
  bk-apigateway-operator [command]                                                                                                                                                                      
                                                                                                                                                                                                        
Available Commands:                                                                                                                                                                                     
  completion  Generate the autocompletion script for the specified shell                                                                                                                                
  help        Help about any command                                                                                                                                                                    
  list-apigw  list resources in apigw                                                                                                                                                                   
  list-apisix list resources in apisix                                                                                                                                                                  
  version     Print the version number of operator                                                                                                                                                      
                                                                                                                                                                                                        
Flags:                                                                                                                                                                                                  
  -c, --config string   config file (default is config.yml;required)                                                                                                                                    
  -h, --help            help for bk-apigateway-operator                                                                                                                                                 
      --viper           Use Viper for configuration (default true)
```

### list-apigw
Provide control plane resource function query
```shell
list resources in apigw                                                                                                                                                                                 
                                                                                                                                                                                                        
Usage:                                                                                                                                                                                                  
  bk-apigateway-operator list-apigw [flags]                                                                                                                                                             
                                                                                                                                                                                                        
Flags:                                                                                                                                                                                                  
  -c, --config string          config file (default is config.yml;required)                                                                                                                             
      --count                  gateway resources count                                                                                                                                                  
      --current-version        gateway stage version                                                                                                                                                    
      --gateway_name string    gateway name for list apigw command                                                                                                                                      
  -h, --help                   help for list-apigw                                                                                                                                                      
      --resource_id int        resource ID for list apigw command                                                                                                                                       
      --resource_name string   resource name for list apigw command                                                                                                                                     
      --stage_name string      stage name for list apigw command                                                                                                                                        
      --viper                  Use Viper for configuration (default true)                                                                                                                               
  -w, --write-out string       response write out format (simple, json, yaml) (default "json")                                                                                                          
```

### list-apisix
Provide data plane gateway resource function query
```shell
list resources in apisix                                                                                                                                                                                
                                                                                                                                                                                                        
Usage:                                                                                                                                                                                                  
  bk-apigateway-operator list-apisix [flags]                                                                                                                                                            
                                                                                                                                                                                                        
Flags:                                                                                                                                                                                                  
  -c, --config string          config file (default is config.yml;required)                                                                                                                             
      --count                  gateway resources count                                                                                                                                                  
      --current-version        gateway stage version                                                                                                                                                    
      --gateway_name string    gateway name for list apisix command                                                                                                                                     
  -h, --help                   help for list-apisix                                                                                                                                                     
      --resource_id int        resource ID for list apisix command                                                                                                                                      
      --resource_name string   resource name for list apisix command                                                                                                                                    
      --stage_name string      stage name for list apisix command                                                                                                                                       
      --viper                  Use Viper for configuration (default true)                                                                                                                               
  -w, --write-out string       response write out format (simple, json, yaml) (default "json")    
```