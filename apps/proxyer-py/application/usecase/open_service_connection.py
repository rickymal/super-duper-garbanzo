

# Responsible for receive the request with ports and open a new server to work
class OpenServiceConnectionUseCase:
    def __init__(self, service_repository, service_factory):
        self.service_repository = service_repository
        self.service_factory = service_factory

    def execute(self, request):
        # Validate the request
        if not request.ports:
            raise ValueError("Ports are required to open a new service connection.")

        # Create a new service instance
        service = self.service_factory.create_service(request.ports)

        # Save the new service instance to the repository
        self.service_repository.save(service)

        return service