
# # region Debug Actions
#     def test_email_started(self):
#         theme = self.theme_service.get_theme(self.active_theme_name)
        
#         # Check if there's actually anyone to send to for the active theme
#         subs = self.notification_service._load_subscribers().get(theme.name, [])
#         if not subs:
#             return False, f"No subscribers for {theme.name} today."

#         context = {
#             "theme_name": theme.name,
#             "main_message": f"[TEST] {theme.name} has just been started!"
#         }
#         if hasattr(self.tracking_service, '_get_newsletter_content'):
#             context.update(self.tracking_service._get_newsletter_content(theme))
        
#         try:
#             self.notification_service.send_notification(theme.name, context)
#             return True, f"'Started' email sent to {theme.name} subs!"
#         except Exception as e:
#             return False, f"Failed: {str(e)}"

#     def test_email_ready(self):
#         theme = self.theme_service.get_theme(self.active_theme_name)
        
#         subs = self.notification_service._load_subscribers().get(theme.name, [])
#         if not subs:
#             return False, f"No subscribers for {theme.name} today."

#         context = {
#             "theme_name": theme.name,
#             "main_message": f"[TEST] {theme.name} is now ready! Enjoy!"
#         }
#         if hasattr(self.tracking_service, '_get_newsletter_content'):
#             context.update(self.tracking_service._get_newsletter_content(theme))
            
#         try:
#             self.notification_service.send_notification(theme.name, context)
#             return True, f"'Ready' email sent to {theme.name} subs!"
#         except Exception as e:
#             return False, f"Failed: {str(e)}"
# # endregion