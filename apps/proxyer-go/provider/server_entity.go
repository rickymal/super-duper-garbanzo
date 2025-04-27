package provider

type Status uint

const (
	Unknown Status = iota
	Online
	Offline
	Busy
	Disabled
	Unreachable
	Timeout
	NotFound
	Invalid
	NotSupported
	NotImplemented
	NotAuthorized
	NotConfigured
	NotAvailable
	NotConnected
	NotResponding
	NotReachable
)

type ServerDao struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	IP          string `json:"ip"`
	Port        int    `json:"port"`
	Status      Status `json:"status"`
	//Username    string `json:"username"`
	//Password    string `json:"password"`
	//SSHKey      string `json:"ssh_key"`
	//SSHKeyName  string `json:"ssh_key_name"`
	//SSHKeyPath  string `json:"ssh_key_path"`
	//SSHKeyType  string `json:"ssh_key_type"`
	//SSHKeyPass  string `json:"ssh_key_pass"`
	//SSHKeyFile  string `json:"ssh_key_file"`
}
