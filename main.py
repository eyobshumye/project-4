# Import necessary libraries
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivy.uix.camera import Camera
from kivy.uix.image import Image
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivymd.uix.list import MDList, TwoLineListItem
from kivymd.uix.navigationdrawer import MDNavigationDrawer

import requests
import os
import uuid
from PIL import Image as PILImage



# Define your screens
class LoginScreen(Screen):
    def login(self):
        # Get the username and password from text inputs
        username = self.ids.username_input.text
        password = self.ids.password_input.text

        # Send a request to your PHP login processor script
        # (You need to set the appropriate URL)
        response = requests.post('http://192.168.134.42/icpm/app_login.php', data={'username': username, 'userpassword': password})
        
        if response.status_code == 200:
            # Check the response content or status to determine if login was successful
            content = response.text
            if 'Login successful' in content:
                self.show_popup("Login Successful")
                self.manager.current = 'project_list'  # Navigate to the project list screen on success
            else:
                self.show_popup("Login Failed")
        else:
            self.show_popup("Failed to connect to the server")

    def show_popup(self, message):
        # Create a popup to display the login result
        popup_content = BoxLayout(orientation="vertical")
        popup_content.add_widget(Label(text=message))
        
        # Create a close button to dismiss the popup
        close_button = MDRaisedButton(text="Close")
        close_button.bind(on_release=self.dismiss_popup)
        popup_content.add_widget(close_button)
        
        self.popup = Popup(title='Login Result', content=popup_content, size_hint=(None, None), size=(300, 200))
        self.popup.open()

    def dismiss_popup(self, instance):
        # Dismiss the popup when the close button is pressed
        self.popup.dismiss()

class ProjectListScreen(Screen):
    def populate_project_list(self):
        # Create an MDList to hold the project codes
        project_list = MDList()
        
        # Send a request to your PHP script to fetch project data
        response = requests.get('http://192.168.134.42/icpm/app_project_code.php')

        if response.status_code == 200:
            project_data = response.json()
            for project in project_data:
                item = TwoLineListItem(
                    text=project['project_code'],
                    secondary_text=project['project_description']
                )
                item.bind(on_release=self.on_project_click)  # Bind the release event
                project_list.add_widget(item)
        
        # Add the project list to the screen
        self.ids.project_list.add_widget(project_list)

    def on_project_click(self, instance):
        # Get the selected project code from the clicked item
        selected_project_code = instance.text

        # Set the value of the project_code_input field in the FormUploadScreen
        form_upload_screen = self.manager.get_screen('form_upload')
        form_upload_screen.ids.project_code_input.text = selected_project_code

        # Navigate to the form upload screen
        self.manager.current = 'form_upload'

class FormUploadScreen(Screen):
    captured_image_path = ""

    def open_camera(self):
        # Activate the camera before navigating to CameraScreen
        camera_screen = self.manager.get_screen('camera_screen')
        camera_screen.ids.camera.play = True

        # Navigate to the CameraScreen
        self.manager.current = 'camera_screen'

    def capture_image(self):
        # Capture the image and set it in the ShowImageScreen
        self.captured_image = self.ids.camera.texture
        self.manager.get_screen('show_image').ids.image.texture = self.captured_image

        # Navigate to the ShowImageScreen
        self.manager.current = 'show_image'

    # Function to submit data to PHP and MySQL
    def submit_data(self):
        # Get the values of the text input fields
        project_code = self.ids.project_code_input.text
        project_description = self.ids.project_description_input.text

        # Check if all required fields are filled
        if not project_code or not project_description:
            self.show_popup("Please fill in all fields.")
            return

        # Check if an image has been captured
        if not self.captured_image_path:
            self.show_popup("Please capture an image.")
            return

        # Now, send the image and text data to your PHP backend
        self.send_data_to_php(self.captured_image_path, project_code, project_description)


    # Function to send data to PHP backend
    def send_data_to_php(self, image_path, project_code, project_description):
        # Define the URL of your PHP script on the server
        php_url = 'http://192.168.134.42/icpm/app_upload.php'  # Replace with your actual URL
        
        # Prepare the data to send, including the image file
        data = {
            'project_code': project_code,
            'project_description': project_description,
        }
        
        # Create a dictionary for the files to be sent
        files = {'image': open(image_path, 'rb')}
        
        # Send the data and image using a POST request
        response = requests.post(php_url, data=data, files=files)
        
        # Check the response from the server
        if response.status_code == 200:
            self.show_popup("Image and data uploaded successfully!")
        else:
            self.show_popup("Failed to upload image and data to the server")

    def show_popup(self, message):
        # Create a popup to display the result
        popup_content = BoxLayout(orientation="vertical")
        popup_content.add_widget(Label(text=message))
        
        # Create a close button to dismiss the popup
        close_button = MDRaisedButton(text="Close")
        close_button.bind(on_release=self.dismiss_popup)
        popup_content.add_widget(close_button)
        
        self.popup = Popup(title='Result', content=popup_content, size_hint=(None, None), size=(300, 200))
        self.popup.open()

    def dismiss_popup(self, instance):
        # Dismiss the popup when the close button is pressed
        self.popup.dismiss()

    def set_captured_image(self, image_texture):
        # Save the image as a file
        if image_texture:
            image_path = "captured_images"  # Change this to your desired directory
            unique_filename = "image_{0}.jpg".format(uuid.uuid4())  # Generate a unique filename with .jpg extension
            full_image_path = os.path.join(image_path, unique_filename)

            pil_image = PILImage.frombytes('RGBA', image_texture.size, image_texture.pixels)
            pil_image = pil_image.convert('RGB')
            pil_image.save(full_image_path, 'JPEG')

            # Set the captured_image_path to the saved image path
            self.captured_image_path = full_image_path

            # Set the source of the Image widget to the saved image
            self.ids.captured_image.source = full_image_path


class CameraScreen(Screen):
    def capture_image(self):
        camera = self.ids.camera
        image_texture = camera.texture
        show_image_screen = self.manager.get_screen('show_image')
        show_image_screen.set_captured_image(image_texture)

        # Deactivate the camera to prevent capturing another image
        camera.play = False

        self.manager.current = 'show_image'


class ShowImageScreen(Screen):
    def set_captured_image(self, image_texture):
        # Update the image in the UI
        self.ids.image.texture = image_texture

    def discard_image(self):
        # Set camera.play to False before navigating back to CameraScreen
        camera_screen = self.manager.get_screen('camera_screen')
        camera_screen.ids.camera.play = True
        
        # Clear the captured image in the ShowImageScreen
        self.ids.image.texture = None
        
        # Clear the captured image in the FormUploadScreen
        form_upload_screen = self.manager.get_screen('form_upload')
        form_upload_screen.ids.captured_image.source = ""

        # Navigate back to the CameraScreen
        self.manager.current = 'camera_screen'

    def keep_image(self):
        # Navigate back to the FormUploadScreen, keeping the captured image
        self.manager.current = 'form_upload'
        self.manager.get_screen('form_upload').set_captured_image(self.ids.image.texture)



class EnatApp(MDApp):
    captured_image = None  # Store the captured image

    def build(self):

        self.screen_manager = ScreenManager()
        self.screen_manager.add_widget(LoginScreen(name='login'))
        self.screen_manager.add_widget(ProjectListScreen(name='project_list'))
        self.screen_manager.add_widget(FormUploadScreen(name='form_upload'))
        self.screen_manager.add_widget(CameraScreen(name='camera_screen'))
        self.screen_manager.add_widget(ShowImageScreen(name='show_image'))
        return Builder.load_file("content.kv")

    def on_start(self):
        self.screen_manager.current = 'login'

    def navigation_draw(self):
        if hasattr(self, 'ids') and 'nav_drawer' in self.ids:
            if self.ids.nav_drawer.state == "open":
                self.ids.nav_drawer.set_state("close")
            else:
                self.ids.nav_drawer.set_state("open")

    def show_user_profile(self):
        # Implement your user profile logic here
        pass

    def drawer_item_click(self, item_text):
        # Handle the click on items in the drawer
        if item_text == 'Item 1':
            # Implement action for Item 1
            pass
        elif item_text == 'Item 2':
            # Implement action for Item 2
            pass


if __name__ == '__main__':
    app = EnatApp()
    app.run()
